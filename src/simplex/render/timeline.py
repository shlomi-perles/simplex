"""Timeline discovery, composition, packaging, and manifest assembly."""

from __future__ import annotations

import contextlib
import datetime as dt
import json
import shutil
import subprocess
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any, Literal, cast

import av
import av.error

from simplex.deck.config import DeckConfig
from simplex.manifest import (
    Cue,
    DeckInfo,
    DeckManifest,
    ManifestAssets,
    ManifestCompat,
    ManifestExports,
    ProgressiveMode,
    SceneCue,
    SceneCueManifest,
    ThemeMedia,
    ThemeTimeline,
)
from simplex.section import CueKind

DEFAULT_FPS = 60
DEFAULT_SEGMENT_DURATION = 4
DEFAULT_CSS_FILTER = "invert(1) hue-rotate(180deg)"


@dataclass(frozen=True, slots=True)
class RenderedUnit:
    scene: str
    unit: str
    source_file: Path
    video: Path | None
    fps: int
    duration: float
    duration_frames: int
    cues: tuple[SceneCue, ...]


@dataclass(frozen=True, slots=True)
class PackagedTheme:
    theme: ThemeTimeline
    progressive_mode: ProgressiveMode
    hls_available: bool
    warnings: tuple[str, ...]
    lecture_mp4: Path | None


def load_units(deck: DeckConfig, *, media_dir: Path) -> tuple[RenderedUnit, ...]:
    """Return rendered scene units in deck entrypoint order."""
    units: list[RenderedUnit] = []
    source_files = {
        class_name: group.source_file
        for group in deck.resolve_entrypoints()
        for class_name in group.scene_names
    }
    for class_name in deck.scene_class_names:
        source_file = source_files[class_name]
        video = _find_scene_video(media_dir, source_file, class_name)
        video_duration = _media_duration(video) if video is not None else 0.0
        cue_manifest = _read_cue_manifest(media_dir, class_name)
        cues: tuple[SceneCue, ...]
        if cue_manifest is None:
            fps = DEFAULT_FPS
            duration = video_duration
            cues = (_implicit_scene_cue(class_name, source_file, fps=fps, duration=duration),)
        else:
            fps = cue_manifest.fps or DEFAULT_FPS
            duration = max(cue_manifest.duration, video_duration)
            cues = _normalize_scene_cues(cue_manifest.cues)
        duration_frames = max(
            _frames(duration, fps),
            max((cue.end_frame for cue in cues), default=0),
        )
        units.append(
            RenderedUnit(
                scene=class_name,
                unit=cues[0].unit if cues else f"{source_file.stem}:{class_name}",
                source_file=source_file,
                video=video,
                fps=fps,
                duration=duration,
                duration_frames=duration_frames,
                cues=cues,
            )
        )
    return tuple(units)


def rebase_cues(units: tuple[RenderedUnit, ...], *, fps: int | None = None) -> tuple[Cue, ...]:
    """Rebase unit-local cue times into one canonical lecture timeline."""
    if not units:
        return ()
    fps = fps or units[0].fps or DEFAULT_FPS
    frame_offset = 0
    current_main_id: str | None = None
    current_main_cue_number = 0
    used_ids: set[str] = set()
    cues: list[Cue] = []
    for unit in units:
        for cue in unit.cues:
            cue_id = cue.id
            if cue.kind.is_slide:
                if cue.auto_id:
                    cue_id = _dedupe_id(_slugify(cue.title), used_ids)
                current_main_id = cue_id
                current_main_cue_number = 1
            elif cue.auto_id:
                if current_main_id is None:
                    current_main_id = _dedupe_id(_slugify(_humanise(unit.scene)), used_ids)
                    current_main_cue_number = 1
                current_main_cue_number += 1
                cue_id = _dedupe_id(f"{current_main_id}-{current_main_cue_number}", used_ids)
            used_ids.add(cue_id)
            start_frame = frame_offset + cue.start_frame
            end_frame = frame_offset + cue.end_frame
            cues.append(
                Cue(
                    id=cue_id,
                    ordinal=len(cues) + 1,
                    kind=cue.kind,
                    title=cue.title,
                    unit=cue.unit,
                    start_frame=start_frame,
                    end_frame=end_frame,
                    start=start_frame / fps,
                    end=end_frame / fps,
                    notes_ref=f"notes.html#{cue_id}",
                )
            )
        frame_offset += unit.duration_frames
    return tuple(cues)


def validate_theme_cues(
    reference: tuple[RenderedUnit, ...],
    candidate: tuple[RenderedUnit, ...],
    *,
    theme_id: str,
) -> tuple[str, ...]:
    """Validate cue id order across themes. Returns warnings for duration drift."""
    ref_ids = tuple(cue.id for unit in reference for cue in unit.cues)
    candidate_ids = tuple(cue.id for unit in candidate for cue in unit.cues)
    if ref_ids != candidate_ids:
        raise ValueError(
            f"theme {theme_id!r} cue ids do not match the default theme: "
            f"{candidate_ids!r} != {ref_ids!r}"
        )
    warnings: list[str] = []
    ref_durations = tuple(unit.duration_frames for unit in reference)
    candidate_durations = tuple(unit.duration_frames for unit in candidate)
    if ref_durations != candidate_durations:
        warnings.append(
            f"theme {theme_id!r} duration differs from the default theme; "
            "cue-local progress mapping will use cue ids and seconds"
        )
    return tuple(warnings)


def package_theme(
    *,
    theme_id: str,
    label: str,
    background: str | None = None,
    units: tuple[RenderedUnit, ...],
    cues: tuple[Cue, ...],
    output_dir: Path,
    media_href_prefix: str,
    segment_duration: int = DEFAULT_SEGMENT_DURATION,
) -> PackagedTheme:
    """Compose scene units and package one theme timeline."""
    output_dir.mkdir(parents=True, exist_ok=True)
    videos = tuple(unit.video for unit in units if unit.video is not None and unit.video.exists())
    warnings: list[str] = []
    lecture = output_dir / "lecture.mp4"
    source = output_dir / "_timeline_source.mp4"
    progressive_mode: ProgressiveMode = "missing"
    hls_available = False
    ffmpeg_path = shutil.which("ffmpeg")

    if not videos:
        warnings.append(f"theme {theme_id!r} has no rendered scene videos")
    else:
        if _compose_with_pyav(videos, lecture):
            progressive_mode = "copy" if len(videos) == 1 else "pyav"
        elif ffmpeg_path is not None and _compose_with_ffmpeg(videos, source):
            warnings.append(f"PyAV could not compose theme {theme_id!r}; used ffmpeg fallback")
            mode: Literal["hybrid_fragmented", "faststart"] = (
                "hybrid_fragmented" if _ffmpeg_supports_hybrid_mp4() else "faststart"
            )
            progressive_mode = mode
            if not _write_progressive_mp4(source, lecture, mode):
                warnings.append(f"ffmpeg could not write progressive MP4 for theme {theme_id!r}")
                if source.exists():
                    shutil.copy2(source, lecture)
                    progressive_mode = "copy"
        else:
            if ffmpeg_path is None:
                warnings.append(f"PyAV could not compose theme {theme_id!r}; ffmpeg is unavailable")
            else:
                warnings.append(f"PyAV and ffmpeg could not compose theme {theme_id!r}")

    if lecture.exists():
        hls_available = _write_hls_pyav(
            lecture,
            output_dir / "hls",
            segment_duration=segment_duration,
        )
        if not hls_available and ffmpeg_path is not None:
            hls_available = _write_hls_ffmpeg(
                lecture,
                output_dir / "hls",
                fps=units[0].fps if units else DEFAULT_FPS,
                segment_duration=segment_duration,
                keyframes=_keyframe_seconds(cues),
            )
            if hls_available:
                warnings.append(
                    f"PyAV HLS/CMAF failed for theme {theme_id!r}; used ffmpeg fallback"
                )
        if not hls_available:
            warnings.append(
                f"HLS/CMAF packaging failed for theme {theme_id!r}; MP4 fallback remains"
            )

    if lecture.exists() and not hls_available:
        warnings.append(f"theme {theme_id!r} will rely on the progressive MP4 fallback")

    media = ThemeMedia(
        hls=f"{media_href_prefix}/hls/master.m3u8" if hls_available else None,
        mp4=f"{media_href_prefix}/lecture.mp4" if lecture.exists() else None,
    )
    theme = ThemeTimeline(
        id=theme_id,
        label=label,
        strategy="rendered",
        media=media,
        duration=_theme_duration(units, cues),
        background=background,
    )
    return PackagedTheme(
        theme=theme,
        progressive_mode=progressive_mode,
        hls_available=hls_available,
        warnings=tuple(warnings),
        lecture_mp4=lecture if lecture.exists() else None,
    )


def css_filter_fallback_theme(
    *,
    theme_id: str,
    label: str,
    source: ThemeTimeline,
    background: str | None = None,
    css_filter: str = DEFAULT_CSS_FILTER,
) -> ThemeTimeline:
    return ThemeTimeline(
        id=theme_id,
        label=label,
        strategy="css_filter_fallback",
        source_theme=source.id,
        css_filter=css_filter,
        duration=source.duration,
        background=background,
        media=source.media,
    )


def build_manifest(
    deck: DeckConfig,
    *,
    cues: tuple[Cue, ...],
    themes: tuple[ThemeTimeline, ...],
    warnings: tuple[str, ...],
    exports: ManifestExports | None = None,
    compat: ManifestCompat | None = None,
    media_base_url: str = ".",
    fps: int = DEFAULT_FPS,
) -> DeckManifest:
    duration = max(
        [cue.end for cue in cues] + [theme.duration for theme in themes] + [0.0],
    )
    return DeckManifest(
        deck=DeckInfo(slug=deck.slug, title=deck.title),
        generated_at=dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat(),
        fps=fps,
        duration=duration,
        cues=cues,
        themes=themes,
        assets=ManifestAssets(base_url=media_base_url or "."),
        exports=exports or ManifestExports(),
        budget_warnings=warnings,
        compat=compat or ManifestCompat(),
    )


def prefix_media_urls(theme: ThemeTimeline, media_base_url: str) -> ThemeTimeline:
    """Return ``theme`` with media URLs prefixed by an optional external base."""
    if not media_base_url:
        return theme
    base = media_base_url.rstrip("/")
    media = ThemeMedia(
        hls=_prefix(base, theme.media.hls),
        mp4=_prefix(base, theme.media.mp4),
    )
    return theme.model_copy(update={"media": media})


def _prefix(base: str, value: str | None) -> str | None:
    if value is None:
        return None
    if value.startswith(("http://", "https://", "/")):
        return value
    return f"{base}/{value.lstrip('/')}"


def media_duration(video: Path | None) -> float:
    return _media_duration(video)


def _find_scene_video(media_dir: Path, source_file: Path, scene: str) -> Path | None:
    matches = sorted((media_dir / "videos" / source_file.stem).glob(f"*/{scene}.mp4"))
    return matches[0] if matches else None


def _read_cue_manifest(media_dir: Path, scene: str) -> SceneCueManifest | None:
    path = media_dir / "simplex-cues" / f"{scene}.json"
    if not path.exists():
        return None
    with contextlib.suppress(OSError, ValueError, json.JSONDecodeError):
        return SceneCueManifest.read(path)
    return None


def _implicit_scene_cue(scene: str, source_file: Path, *, fps: int, duration: float) -> SceneCue:
    title = _humanise(scene)
    return SceneCue(
        id=_slugify(title),
        kind=CueKind.SLIDE,
        title=title,
        unit=f"{source_file.stem}:{scene}",
        start_frame=0,
        end_frame=_frames(duration, fps),
        start=0.0,
        end=duration,
        auto_id=True,
    )


def _normalize_scene_cues(cues: tuple[SceneCue, ...]) -> tuple[SceneCue, ...]:
    """Migrate stale auto ``next_slide`` cue manifests.

    Older Simplex builds recorded the first legacy ``next_slide()`` marker as
    the start of the first cue. In that authoring style the marker is actually
    the first pause, so leading media belongs to the main cue and the old first
    cue becomes the first fragment. Explicit cue ids keep their authored start.
    """
    if not cues:
        return cues
    first = cues[0]
    if first.start_frame <= 0 and first.start <= 0:
        return cues
    if not first.auto_id or not first.kind.is_slide:
        return cues
    leading = first.model_copy(
        update={
            "start_frame": 0,
            "end_frame": first.start_frame,
            "start": 0.0,
            "end": first.start,
        }
    )
    shifted = _shift_legacy_first_fragment(first, base_id=leading.id, number=2)
    if shifted is None:
        return (leading, *cues[1:])
    return (
        leading,
        shifted,
        *_shift_following_legacy_subcues(cues[1:], base_id=leading.id),
    )


def _shift_legacy_first_fragment(
    cue: SceneCue,
    *,
    base_id: str,
    number: int,
) -> SceneCue | None:
    if cue.end_frame <= cue.start_frame and cue.end <= cue.start:
        return None
    return cue.model_copy(
        update={
            "id": f"{base_id}-{number}",
            "kind": CueKind.FRAGMENT,
            "title": f"{cue.title} Detail 1",
        }
    )


def _shift_auto_subcue(cue: SceneCue, *, base_id: str, number: int) -> SceneCue:
    if not cue.auto_id or cue.kind.is_slide:
        return cue
    return cue.model_copy(update={"id": f"{base_id}-{number}"})


def _shift_following_legacy_subcues(
    cues: tuple[SceneCue, ...],
    *,
    base_id: str,
) -> tuple[SceneCue, ...]:
    shifted: list[SceneCue] = []
    number = 3
    for index, cue in enumerate(cues):
        if cue.kind.is_slide:
            shifted.extend(cues[index:])
            break
        shifted.append(_shift_auto_subcue(cue, base_id=base_id, number=number))
        number += 1
    return tuple(shifted)


def _frames(seconds: float, fps: int) -> int:
    return max(0, round(seconds * fps))


def _humanise(camel: str) -> str:
    if not camel:
        return camel
    out = [camel[0]]
    for ch in camel[1:]:
        if ch.isupper() and out[-1] != " ":
            out.append(" ")
        out.append(ch)
    return "".join(out)


def _slugify(value: str) -> str:
    import re

    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-") or "cue"


def _dedupe_id(cue_id: str, used_ids: set[str]) -> str:
    if cue_id not in used_ids:
        return cue_id
    index = 2
    while f"{cue_id}-{index}" in used_ids:
        index += 1
    return f"{cue_id}-{index}"


def _media_duration(video: Path | None) -> float:
    if video is None or not video.exists():
        return 0.0
    try:
        with av.open(str(video)) as container:
            if container.duration is not None:
                return float(container.duration / 1_000_000)
            stream = container.streams.video[0]
            if stream.duration is not None and stream.time_base is not None:
                return float(stream.duration * stream.time_base)
    except (av.error.FFmpegError, IndexError, OSError, ValueError):
        return 0.0
    return 0.0


def _compose_with_ffmpeg(videos: tuple[Path, ...], source: Path) -> bool:
    if not videos:
        return False
    source.parent.mkdir(parents=True, exist_ok=True)
    if len(videos) == 1:
        shutil.copy2(videos[0], source)
        return True
    file_list = source.with_name("_concat.txt")
    file_list.write_text(
        "".join(f"file '{video.resolve().as_posix()}'\n" for video in videos),
        encoding="utf-8",
    )
    args = [
        "ffmpeg",
        "-y",
        "-loglevel",
        "error",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(file_list),
        "-c",
        "copy",
        str(source),
    ]
    with contextlib.suppress(subprocess.SubprocessError, FileNotFoundError):
        subprocess.run(args, check=True, timeout=120)
        return source.exists()
    return False


def _compose_with_pyav(videos: tuple[Path, ...], lecture: Path) -> bool:
    """Compose scene videos into the progressive MP4 used by the player."""
    if not videos:
        return False
    try:
        lecture.parent.mkdir(parents=True, exist_ok=True)
        if len(videos) == 1:
            shutil.copy2(videos[0], lecture)
            return lecture.exists()
        first = _video_stream_info(videos[0])
        if first is None:
            return False
        width, height, rate = first
        with av.open(str(lecture), mode="w") as output:
            stream = output.add_stream("h264", rate=rate)
            stream.width = width
            stream.height = height
            stream.pix_fmt = "yuv420p"
            stream.codec_context.gop_size = 1
            stream.codec_context.max_b_frames = 0
            stream.options = {"preset": "veryfast", "tune": "zerolatency"}
            pts = 0
            time_base = Fraction(rate.denominator, rate.numerator)
            for video in videos:
                with av.open(str(video)) as source:
                    in_stream = source.streams.video[0]
                    for frame in source.decode(in_stream):
                        frame = frame.reformat(width=width, height=height, format="yuv420p")
                        frame.pts = pts
                        frame.time_base = time_base
                        pts += 1
                        for packet in stream.encode(frame):
                            output.mux(packet)
            for packet in stream.encode():
                output.mux(packet)
    except (av.error.FFmpegError, IndexError, OSError, ValueError, ZeroDivisionError):
        return False
    return lecture.exists()


def _video_stream_info(video: Path) -> tuple[int, int, Fraction] | None:
    try:
        with av.open(str(video)) as container:
            stream = container.streams.video[0]
            rate = stream.average_rate or stream.base_rate
            if rate is None:
                return (stream.width, stream.height, Fraction(DEFAULT_FPS, 1))
            return (stream.width, stream.height, Fraction(rate))
    except (av.error.FFmpegError, IndexError, OSError, ValueError):
        return None


def _ffmpeg_supports_hybrid_mp4() -> bool:
    with contextlib.suppress(subprocess.SubprocessError, FileNotFoundError):
        result = subprocess.run(
            ["ffmpeg", "-hide_banner", "-h", "muxer=mp4"],
            check=True,
            capture_output=True,
            text=True,
            timeout=15,
        )
        return "hybrid_fragmented" in (result.stdout + result.stderr)
    return False


def _write_progressive_mp4(
    source: Path,
    lecture: Path,
    mode: Literal["hybrid_fragmented", "faststart"],
) -> bool:
    movflags = "+hybrid_fragmented" if mode == "hybrid_fragmented" else "+faststart"
    args = [
        "ffmpeg",
        "-y",
        "-loglevel",
        "error",
        "-i",
        str(source),
        "-map",
        "0:v:0",
        "-map",
        "0:a?",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-preset",
        "veryfast",
        "-crf",
        "20",
        "-c:a",
        "aac",
        "-b:a",
        "128k",
        "-movflags",
        movflags,
        str(lecture),
    ]
    with contextlib.suppress(subprocess.SubprocessError, FileNotFoundError):
        subprocess.run(args, check=True, timeout=180)
        return lecture.exists()
    return False


def _write_hls_pyav(
    lecture: Path,
    hls_dir: Path,
    *,
    segment_duration: int,
) -> bool:
    try:
        cast(Any, av).format.ContainerFormat("hls", "w")
    except (av.error.FFmpegError, ValueError):
        return False

    rendition = hls_dir / "1080p"
    _reset_hls_dir(hls_dir)
    rendition.mkdir(parents=True, exist_ok=True)
    source = lecture.resolve()
    playlist = rendition / "media.m3u8"
    options = {
        "hls_time": str(segment_duration),
        "hls_playlist_type": "vod",
        "hls_segment_type": "fmp4",
        "hls_fmp4_init_filename": "init.mp4",
        "hls_segment_filename": "seg-%05d.m4s",
        "hls_flags": "independent_segments",
    }
    try:
        with (
            contextlib.chdir(rendition),
            av.open(str(source)) as input_,
            av.open("media.m3u8", mode="w", format="hls", options=options) as output,
        ):
            input_streams = tuple(
                stream for stream in input_.streams if stream.type in {"video", "audio"}
            )
            if not input_streams:
                return False
            stream_map = {
                stream.index: _add_stream_from_template(output, stream) for stream in input_streams
            }
            for packet in input_.demux(*input_streams):
                if packet.dts is None:
                    continue
                out_stream = stream_map.get(packet.stream.index)
                if out_stream is None:
                    continue
                packet.stream = out_stream
                output.mux(packet)
    except (av.error.FFmpegError, AttributeError, IndexError, OSError, TypeError, ValueError):
        return False
    if not playlist.exists() or not (rendition / "init.mp4").exists():
        return False
    if not any(rendition.glob("*.m4s")):
        return False
    _write_hls_master(hls_dir)
    return True


def _add_stream_from_template(
    output: Any,
    stream: Any,
) -> Any:
    try:
        return output.add_stream(template=stream)
    except TypeError:
        return output.add_stream_from_template(stream)


def _write_hls_ffmpeg(
    lecture: Path,
    hls_dir: Path,
    *,
    fps: int,
    segment_duration: int,
    keyframes: tuple[float, ...],
) -> bool:
    rendition = hls_dir / "1080p"
    _reset_hls_dir(hls_dir)
    rendition.mkdir(parents=True, exist_ok=True)
    playlist = rendition / "media.m3u8"
    keyframe_arg = ",".join(f"{value:.6f}" for value in keyframes if value >= 0)
    gop = max(1, fps * segment_duration)
    args = [
        "ffmpeg",
        "-y",
        "-loglevel",
        "error",
        "-i",
        str(lecture),
        "-map",
        "0:v:0",
        "-map",
        "0:a?",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-preset",
        "veryfast",
        "-crf",
        "21",
        "-g",
        str(gop),
        "-sc_threshold",
        "0",
        "-c:a",
        "aac",
        "-b:a",
        "128k",
        "-f",
        "hls",
        "-hls_time",
        str(segment_duration),
        "-hls_playlist_type",
        "vod",
        "-hls_segment_type",
        "fmp4",
        "-hls_fmp4_init_filename",
        "init.mp4",
        "-hls_segment_filename",
        str(rendition / "seg-%05d.m4s"),
    ]
    if keyframe_arg:
        args.extend(["-force_key_frames", keyframe_arg])
    args.append(str(playlist))
    with contextlib.suppress(subprocess.SubprocessError, FileNotFoundError):
        subprocess.run(args, check=True, timeout=240)
        if playlist.exists():
            _write_hls_master(hls_dir)
            return True
    return False


def _reset_hls_dir(hls_dir: Path) -> None:
    if hls_dir.exists():
        shutil.rmtree(hls_dir)


def _write_hls_master(hls_dir: Path) -> None:
    (hls_dir / "master.m3u8").write_text(
        "#EXTM3U\n"
        "#EXT-X-VERSION:7\n"
        '#EXT-X-STREAM-INF:BANDWIDTH=2400000,CODECS="avc1.640028"\n'
        "1080p/media.m3u8\n",
        encoding="utf-8",
    )


def _keyframe_seconds(cues: tuple[Cue, ...]) -> tuple[float, ...]:
    values: list[float] = []
    for cue in cues:
        values.append(cue.start)
        if cue.end > cue.start:
            values.append(cue.end)
    return tuple(sorted({round(value, 6) for value in values}))


def _theme_duration(units: tuple[RenderedUnit, ...], cues: tuple[Cue, ...]) -> float:
    if units:
        fps = units[0].fps or DEFAULT_FPS
        return sum(unit.duration_frames for unit in units) / fps
    return max((cue.end for cue in cues), default=0.0)
