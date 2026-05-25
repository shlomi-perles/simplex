"""Build a main/sub-slide manifest from manim's native sections JSON.

Two JSON sources are read per scene:

- ``<media>/videos/<src_stem>/<quality>/sections/<Scene>.json`` -- written
  by manim's ``SceneFileWriter.combine_to_section_videos`` when
  ``save_sections=True`` is set (the Simplex plugin always sets it). One
  entry per ``Scene.next_section(name=..., section_type=...)`` call. Carries
  ``name``, ``type``, ``video``, plus ffprobe metadata.
- ``<media>/slides/<Scene>.json`` -- written by manim-slides
  (``PresentationConfig``). Carries the per-slide media paths used by the
  RevealJS converter.

The reconciler walks each scene's sections in order and groups consecutive
SUB rows under their preceding MAIN, producing a ``DeckManifest`` of
``MainSlide`` records. The schema (``DeckManifest``, ``MainSlide``,
``Subsection``) lives in :mod:`simplex.manifest` so the Manim plugin and web
pipeline share a single Pydantic definition.
"""

import contextlib
import json
import shutil
import subprocess
from pathlib import Path

from simplex.deck.config import DeckConfig
from simplex.manifest import DeckManifest, MainSlide, Subsection
from simplex.section import SimplexSectionType

# Section types we recognise as a MAIN boundary. Anything not on this list
# (and not the auto-created first ``default.normal``) is attached as a sub.
_MAIN_PREFIX = "simplex.main"
_DEFAULT_NORMAL = "default.normal"


def _coerce_section_type(raw: str, *, as_main: bool) -> SimplexSectionType:
    """Map a raw Manim sections-JSON ``type`` string to a ``SimplexSectionType``.

    Strings that already match a Simplex value (``simplex.main``,
    ``simplex.sub.loop``, ...) round-trip into the matching enum.
    Anything else (``default.normal`` from Manim's auto-created pre-amble,
    user-written custom types) is bucketed into ``MAIN`` or ``SUB`` based
    on the reconciler's classification at the call site.
    """
    try:
        return SimplexSectionType(raw)
    except ValueError:
        return SimplexSectionType.MAIN if as_main else SimplexSectionType.SUB


def _ffprobe_duration(video: Path) -> float:
    """Return the duration of ``video`` in seconds, or 0.0 if ffprobe is missing."""
    if shutil.which("ffprobe") is None or not video.exists():
        return 0.0
    with contextlib.suppress(subprocess.SubprocessError):
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(video),
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=15,
        )
        try:
            return float(result.stdout.strip() or 0.0)
        except ValueError:
            return 0.0
    return 0.0


def _av_duration(video: Path) -> float:
    """Return the duration of ``video`` via PyAV, or 0.0 if unavailable."""
    if not video.exists():
        return 0.0
    try:
        import av
        from av.error import FFmpegError
    except ImportError:
        return 0.0
    try:
        with av.open(str(video)) as container:
            if container.duration is not None:
                return float(container.duration / 1_000_000)
            stream = container.streams.video[0]
            if stream.duration is not None and stream.time_base is not None:
                return float(stream.duration * stream.time_base)
    except (FFmpegError, IndexError, OSError, ValueError):
        return 0.0
    return 0.0


def _media_duration(video: Path) -> float:
    """Return media duration using the fastest available local decoder."""
    return _ffprobe_duration(video) or _av_duration(video)


def _find_sections_json(media_dir: Path, scene: str) -> Path | None:
    """Find ``<media_dir>/videos/*/*/sections/<scene>.json`` (glob over qualities)."""
    if not media_dir.exists():
        return None
    matches = list((media_dir / "videos").glob(f"*/*/sections/{scene}.json"))
    return matches[0] if matches else None


def _find_presentation_json(media_dir: Path, scene: str) -> Path | None:
    """Find ``<media_dir>/slides/<scene>.json`` written by manim-slides."""
    path = media_dir / "slides" / f"{scene}.json"
    return path if path.exists() else None


def _parse_sections(json_path: Path) -> list[dict[str, object]]:
    """Read manim's sections JSON; return a list of section-dict rows.

    Schema (subject to drift): each entry has ``name``, ``type``, ``video``,
    plus ffprobe metadata (``width``, ``height``, ``fps``, ``duration``).
    Missing fields are tolerated.
    """
    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
    except OSError:
        return []
    except json.JSONDecodeError:
        return []
    if not isinstance(data, list):
        return []
    return [row for row in data if isinstance(row, dict)]


def _parse_presentation_slides(json_path: Path) -> list[dict[str, object]]:
    """Read manim-slides PresentationConfig rows from ``slides/<scene>.json``."""
    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
    except OSError:
        return []
    except json.JSONDecodeError:
        return []
    slides = data.get("slides") if isinstance(data, dict) else None
    if not isinstance(slides, list):
        return []
    return [row for row in slides if isinstance(row, dict)]


def _video_path(row: dict[str, object], sections_dir: Path) -> Path | None:
    """Resolve a section's video file. Manim stores the basename in ``video``."""
    raw = row.get("video")
    if not isinstance(raw, str) or not raw:
        return None
    candidate = Path(raw)
    if not candidate.is_absolute():
        candidate = (sections_dir / candidate).resolve()
    return candidate if candidate.exists() else None


def _presentation_video_path(row: dict[str, object], media_dir: Path) -> Path | None:
    """Resolve a manim-slides media path relative to the deck media directory."""
    raw = row.get("file")
    if not isinstance(raw, str) or not raw:
        return None
    candidate = Path(raw.replace("\\", "/"))
    if not candidate.is_absolute():
        candidate = (media_dir / candidate).resolve()
    return candidate if candidate.exists() else None


def _row_duration(row: dict[str, object], video: Path | None) -> float:
    raw = row.get("duration")
    if isinstance(raw, (int, float)):
        return float(raw)
    if isinstance(raw, str):
        try:
            return float(raw)
        except ValueError:
            pass
    return _media_duration(video) if video is not None else 0.0


def _presentation_subsections(media_dir: Path, scene: str) -> tuple[Subsection, ...]:
    """Fallback sub-stops from manim-slides JSON when Manim sections are absent."""
    json_path = _find_presentation_json(media_dir, scene)
    if json_path is None:
        return ()
    subs: list[Subsection] = []
    for i, row in enumerate(_parse_presentation_slides(json_path), start=1):
        video = _presentation_video_path(row, media_dir)
        if video is None:
            continue
        subs.append(
            Subsection(
                name=f"{scene} {i}",
                section_type=(SimplexSectionType.MAIN if i == 1 else SimplexSectionType.SUB),
                video=video,
                duration_s=_media_duration(video),
            )
        )
    return tuple(subs)


def _is_main_section(type_str: str, *, is_first_in_scene: bool) -> bool:
    """Whether this section starts a new MAIN slide.

    Manim creates an implicit ``default.normal`` section at the start of
    every scene. When the very next section is an explicit ``simplex.main``,
    the user clearly intends *that* to be the slide's start, so the leading
    ``default.normal`` is absorbed by the caller as a lead-in subsection
    (handled in ``build_manifest``); ``_is_main_section`` only returns True
    for ``default.normal`` when the scene has no explicit main marker at all.
    """
    if type_str.startswith(_MAIN_PREFIX):
        return True
    return is_first_in_scene and type_str == _DEFAULT_NORMAL


def _absorb_leading_default(rows: list[dict[str, object]]) -> int:
    """Count leading ``default.normal`` rows that should fold into the next main.

    Returns the number of leading rows to attach as lead-in subsections of the
    first ``simplex.main`` row. Returns ``0`` when there's no following
    ``simplex.main`` (so the implicit default stays as its own main).
    """
    count = 0
    while count < len(rows) and str(rows[count].get("type", "")) == _DEFAULT_NORMAL:
        count += 1
    if count == 0 or count >= len(rows):
        return 0
    next_type = str(rows[count].get("type", ""))
    return count if next_type.startswith(_MAIN_PREFIX) else 0


def _humanise(camel: str) -> str:
    if not camel:
        return camel
    out: list[str] = [camel[0]]
    for ch in camel[1:]:
        if ch.isupper() and out[-1] != " ":
            out.append(" ")
        out.append(ch)
    return "".join(out)


def build_manifest(deck: DeckConfig, *, media_dir: Path) -> DeckManifest:
    """Read every scene's sections JSON and return a main/sub tree."""
    main_slides: list[MainSlide] = []
    counter = 1
    for scene in deck.scene_class_names:
        json_path = _find_sections_json(media_dir, scene)
        if json_path is None:
            # Pre-render or test mode: synthesize one empty main per scene.
            subsections = _presentation_subsections(media_dir, scene)
            main_slides.append(
                MainSlide(
                    index=counter,
                    scene=scene,
                    name=_humanise(scene),
                    section_type=SimplexSectionType.MAIN,
                    subsections=subsections,
                )
            )
            counter += 1
            continue
        sections_dir = json_path.parent
        rows = _parse_sections(json_path)
        if not rows:
            main_slides.append(
                MainSlide(
                    index=counter,
                    scene=scene,
                    name=_humanise(scene),
                    section_type=SimplexSectionType.MAIN,
                    subsections=(),
                )
            )
            counter += 1
            continue

        pending_name: str | None = None
        pending_type: SimplexSectionType | None = None
        pending_subs: list[Subsection] = []

        absorbed = _absorb_leading_default(rows)
        lead_in: list[Subsection] = []
        for absorbed_row in rows[:absorbed]:
            type_str = str(absorbed_row.get("type", _DEFAULT_NORMAL))
            video = _video_path(absorbed_row, sections_dir)
            lead_in.append(
                Subsection(
                    name=str(absorbed_row.get("name", "unnamed")),
                    section_type=_coerce_section_type(type_str, as_main=False),
                    video=video,
                    duration_s=_row_duration(absorbed_row, video),
                )
            )

        for i, row in enumerate(rows[absorbed:], start=absorbed):
            type_str = str(row.get("type", _DEFAULT_NORMAL))
            name = str(row.get("name", "unnamed"))
            video = _video_path(row, sections_dir)
            # ``i == 0`` only matters when nothing was absorbed; an absorbed
            # leading default.normal already handled the "first in scene" case.
            is_main = _is_main_section(type_str, is_first_in_scene=(i == 0))
            sub = Subsection(
                name=name,
                section_type=_coerce_section_type(type_str, as_main=is_main),
                video=video,
                duration_s=_row_duration(row, video),
            )
            if is_main:
                if pending_name is not None and pending_type is not None:
                    main_slides.append(
                        MainSlide(
                            index=counter,
                            scene=scene,
                            name=pending_name,
                            section_type=pending_type,
                            subsections=tuple(pending_subs),
                        )
                    )
                    counter += 1
                pending_name = name if type_str != _DEFAULT_NORMAL else _humanise(scene)
                pending_type = (
                    _coerce_section_type(type_str, as_main=True)
                    if type_str.startswith(_MAIN_PREFIX)
                    else SimplexSectionType.MAIN
                )
                pending_subs = [*lead_in, sub]
                lead_in = []
            else:
                pending_subs.append(sub)
        if pending_name is not None and pending_type is not None:
            main_slides.append(
                MainSlide(
                    index=counter,
                    scene=scene,
                    name=pending_name,
                    section_type=pending_type,
                    subsections=tuple(pending_subs),
                )
            )
            counter += 1

    return DeckManifest(deck_slug=deck.slug, main_slides=tuple(main_slides))
