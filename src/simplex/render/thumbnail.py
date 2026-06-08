"""Cue thumbnails, posters, and small deck-card previews from timelines."""

from __future__ import annotations

import contextlib
import hashlib
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

import av
import av.error
from PIL import Image, ImageSequence
from PIL.Image import Resampling

from simplex.deck.config import DeckConfig
from simplex.manifest import Cue

DEFAULT_THUMB_WIDTH = 480
DEFAULT_POSTER_WIDTH = 1280
DEFAULT_GIF_WIDTH = 320
DEFAULT_GIF_FPS = 6
DEFAULT_GIF_MAX_FRAMES = 24
DEFAULT_GIF_COLORS = 64
PLACEHOLDER_NAME = "_placeholder.svg"


@dataclass(frozen=True, slots=True)
class CueImages:
    thumbnails: dict[str, Path]
    posters: dict[str, Path]


def generate_cue_images(
    deck: DeckConfig,
    cues: tuple[Cue, ...],
    *,
    theme_id: str,
    lecture_mp4: Path | None,
    site_deck_dir: Path,
    cache_dir: Path,
    thumbnails: bool,
) -> CueImages:
    """Generate poster images per cue and optional shared thumbnails."""
    poster_dir = site_deck_dir / "posters" / theme_id
    thumb_dir = site_deck_dir / "thumbs"
    cache_root = cache_dir / "cue-images" / deck.slug / theme_id
    poster_dir.mkdir(parents=True, exist_ok=True)
    if thumbnails:
        thumb_dir.mkdir(parents=True, exist_ok=True)
    cache_root.mkdir(parents=True, exist_ok=True)

    posters: dict[str, Path] = {}
    thumbs: dict[str, Path] = {}
    for cue in cues:
        seek_time = _representative_time(cue)
        poster = _one_frame(
            lecture_mp4,
            deck,
            cue,
            poster_dir,
            cache_root,
            width=DEFAULT_POSTER_WIDTH,
            seek_time=seek_time,
            suffix="poster",
        )
        posters[cue.id] = poster.relative_to(site_deck_dir)
        if thumbnails:
            thumb = _one_frame(
                lecture_mp4,
                deck,
                cue,
                thumb_dir,
                cache_root,
                width=DEFAULT_THUMB_WIDTH,
                seek_time=seek_time,
                suffix="thumb",
            )
            thumbs[cue.id] = thumb.relative_to(site_deck_dir)
    return CueImages(thumbnails=thumbs, posters=posters)


def generate_carousel_gif(
    deck: DeckConfig,
    cues: tuple[Cue, ...],
    *,
    lecture_mp4: Path | None,
    site_deck_dir: Path,
    cache_dir: Path,
) -> Path | None:
    """Return a small preview GIF for deck cards when configured."""
    previews_dir = site_deck_dir / "previews"
    cache_root = cache_dir / "carousel-gifs" / deck.slug
    if deck.web.carousel_gif is not None:
        return _copy_gif_override(deck, previews_dir)
    selected = set(deck.web.carousel_gif_slides)
    if not selected or lecture_mp4 is None or not lecture_mp4.exists():
        return None
    selected_times = tuple(
        _representative_time(cue) for cue in cues if cue.kind.is_slide and cue.ordinal in selected
    )
    if not selected_times:
        return None
    previews_dir.mkdir(parents=True, exist_ok=True)
    cache_root.mkdir(parents=True, exist_ok=True)
    key = _video_key(lecture_mp4, deck.slug, f"gif:{selected_times}")
    cached = cache_root / f"{key}.gif"
    dest = previews_dir / f"{key}.gif"
    if cached.exists():
        if not dest.exists():
            shutil.copy2(cached, dest)
        return dest.relative_to(site_deck_dir)
    if _write_preview_gif(lecture_mp4, selected_times, dest):
        shutil.copy2(dest, cached)
        return dest.relative_to(site_deck_dir)
    return None


_PLACEHOLDER_SVG = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 480 270" '
    'preserveAspectRatio="xMidYMid slice" role="img" aria-label="No preview available">'
    '<rect width="480" height="270" fill="#242424"/>'
    '<text x="240" y="142" text-anchor="middle" fill="#8a8a8a" '
    'font-family="system-ui, sans-serif" font-size="18">no preview yet</text>'
    "</svg>"
)


def _placeholder(dest_dir: Path) -> Path:
    placeholder = dest_dir / PLACEHOLDER_NAME
    if not placeholder.exists():
        placeholder.parent.mkdir(parents=True, exist_ok=True)
        placeholder.write_text(_PLACEHOLDER_SVG, encoding="utf-8")
    return placeholder


def _one_frame(
    lecture_mp4: Path | None,
    deck: DeckConfig,
    cue: Cue,
    dest_dir: Path,
    cache_root: Path,
    *,
    width: int,
    seek_time: float,
    suffix: str,
) -> Path:
    if lecture_mp4 is None or not lecture_mp4.exists():
        return _placeholder(dest_dir)
    key = _video_key(lecture_mp4, deck.slug, f"{cue.id}:{seek_time:.3f}:{width}:{suffix}")
    cached = cache_root / f"{key}_{suffix}.jpg"
    dest = dest_dir / f"{cue.id}.jpg"
    if cached.exists():
        if not dest.exists():
            shutil.copy2(cached, dest)
        return dest
    if _extract_frame(lecture_mp4, dest, width=width, seek_time=seek_time):
        shutil.copy2(dest, cached)
        return dest
    return _placeholder(dest_dir)


def _extract_frame(video: Path, dest: Path, *, width: int, seek_time: float) -> bool:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if _try_ffmpeg(video, dest, width=width, seek_time=seek_time):
        return True
    return _try_pyav(video, dest, width=width, seek_time=seek_time)


def _try_ffmpeg(video: Path, dest: Path, *, width: int, seek_time: float) -> bool:
    if shutil.which("ffmpeg") is None:
        return False
    args = [
        "ffmpeg",
        "-y",
        "-loglevel",
        "error",
        "-ss",
        f"{max(0.0, seek_time):.3f}",
        "-i",
        str(video),
        "-vframes",
        "1",
        "-vf",
        f"scale={width}:-2",
        "-q:v",
        "2",
        str(dest),
    ]
    with contextlib.suppress(subprocess.SubprocessError, FileNotFoundError):
        subprocess.run(args, check=True, timeout=30)
        return dest.exists()
    return False


def _try_pyav(video: Path, dest: Path, *, width: int, seek_time: float) -> bool:
    try:
        with av.open(str(video)) as container:
            stream = container.streams.video[0]
            stream.thread_type = "AUTO"
            if stream.time_base is not None:
                container.seek(int(max(0.0, seek_time) / float(stream.time_base)), stream=stream)
            chosen = None
            for frame in container.decode(stream):
                if frame.time is None or frame.time >= seek_time - 0.05:
                    chosen = frame
                    break
            if chosen is None:
                return False
            image = chosen.to_image()
    except (av.error.FFmpegError, IndexError, OSError, ValueError):
        return False
    src_w, src_h = image.size
    if src_w <= 0 or src_h <= 0:
        return False
    target_h = max(1, round(src_h * width / src_w))
    if (src_w, src_h) != (width, target_h):
        image = image.resize((width, target_h), Resampling.LANCZOS)
    image.save(str(dest), "JPEG", quality=85, optimize=True)
    return dest.exists()


def _representative_time(cue: Cue) -> float:
    if cue.end > cue.start:
        return max(cue.start, cue.end - 0.08)
    return cue.start


def _video_key(video: Path, slug: str, suffix: str) -> str:
    stat = video.stat()
    raw = f"{slug}:{video.as_posix()}:{stat.st_mtime_ns}:{stat.st_size}:{suffix}"
    return hashlib.sha256(raw.encode()).hexdigest()[:24]


def _copy_gif_override(deck: DeckConfig, previews_dir: Path) -> Path | None:
    rel = deck.web.carousel_gif
    if rel is None:
        return None
    src = deck.path / rel
    if not src.exists() or src.suffix.lower() != ".gif":
        return None
    previews_dir.mkdir(parents=True, exist_ok=True)
    key = _video_key(src, deck.slug, "override")
    target = previews_dir / f"override_{key}.gif"
    if not target.exists() or target.stat().st_mtime < src.stat().st_mtime:
        shutil.copy2(src, target)
    return target.relative_to(previews_dir.parent)


def _write_preview_gif(video: Path, times: tuple[float, ...], dest: Path) -> bool:
    frames: list[Image.Image] = []
    per_time = max(1, DEFAULT_GIF_MAX_FRAMES // max(1, len(times)))
    for start in times:
        frames.extend(
            _sample_gif_frames(
                video,
                start=start,
                max_frames=per_time,
                width=DEFAULT_GIF_WIDTH,
            )
        )
        if len(frames) >= DEFAULT_GIF_MAX_FRAMES:
            frames = frames[:DEFAULT_GIF_MAX_FRAMES]
            break
    if not frames:
        return False
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        frames[0].save(
            str(dest),
            save_all=True,
            append_images=frames[1:],
            duration=round(1000 / DEFAULT_GIF_FPS),
            loop=0,
            optimize=True,
        )
    except OSError:
        return False
    return dest.exists()


def _sample_gif_frames(
    video: Path, *, start: float, max_frames: int, width: int
) -> list[Image.Image]:
    out: list[Image.Image] = []
    try:
        with av.open(str(video)) as container:
            stream = container.streams.video[0]
            stream.thread_type = "AUTO"
            if stream.time_base is not None:
                container.seek(int(max(0.0, start) / float(stream.time_base)), stream=stream)
            rate = float(stream.average_rate or DEFAULT_GIF_FPS)
            stride = max(1, round(rate / DEFAULT_GIF_FPS))
            for i, frame in enumerate(container.decode(stream)):
                if frame.time is not None and frame.time < start:
                    continue
                if i % stride != 0:
                    continue
                out.append(_gif_frame(frame.to_image(), width=width))
                if len(out) >= max_frames:
                    break
    except (av.error.FFmpegError, IndexError, OSError, ValueError):
        return []
    return out


def _gif_frame(image: Image.Image, *, width: int) -> Image.Image:
    src_w, src_h = image.size
    if src_w > 0 and src_h > 0 and src_w != width:
        target_h = max(1, round(src_h * width / src_w))
        image = image.resize((width, target_h), Resampling.LANCZOS)
    return image.convert("P", palette=Image.Palette.ADAPTIVE, colors=DEFAULT_GIF_COLORS)


def verify_gif(path: Path) -> bool:
    """Small helper for tests and diagnostics."""
    with Image.open(path) as image:
        return sum(1 for _ in ImageSequence.Iterator(image)) >= 1
