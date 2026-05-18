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
``MainSlide`` records. The original flat ``SlideRef``/``manifest.py`` model
is gone -- web templates and thumbnail logic now consume the main/sub tree.
"""

import contextlib
import json
import shutil
import subprocess
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from simplex.deck.config import DeckConfig

# Section types we recognise as a MAIN boundary. Anything not on this list
# (and not the auto-created first ``default.normal``) is attached as a sub.
_MAIN_PREFIX = "simplex.main"
_DEFAULT_NORMAL = "default.normal"


class Subsection(BaseModel):
    """One row in the native sections JSON (main or sub)."""

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)
    name: str
    type_: str
    video: Path | None = None
    duration_s: float = 0.0


class MainSlide(BaseModel):
    """A user-visible main slide with its sub-slides bundled in."""

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)
    index: int
    scene: str
    name: str
    section_type: str
    subsections: tuple[Subsection, ...]
    thumbnail: Path | None = None
    notes: str | None = None

    @property
    def duration_s(self) -> float:
        return sum(s.duration_s for s in self.subsections)


class DeckManifest(BaseModel):
    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)
    deck_slug: str
    main_slides: tuple[MainSlide, ...]

    @property
    def slide_count(self) -> int:
        return len(self.main_slides)

    @property
    def total_duration_s(self) -> float:
        return sum(m.duration_s for m in self.main_slides)


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


def _find_sections_json(media_dir: Path, scene: str) -> Path | None:
    """Find ``<media_dir>/videos/*/*/sections/<scene>.json`` (glob over qualities)."""
    if not media_dir.exists():
        return None
    matches = list((media_dir / "videos").glob(f"*/*/sections/{scene}.json"))
    return matches[0] if matches else None


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


def _video_path(row: dict[str, object], sections_dir: Path) -> Path | None:
    """Resolve a section's video file. Manim stores the basename in ``video``."""
    raw = row.get("video")
    if not isinstance(raw, str) or not raw:
        return None
    candidate = Path(raw)
    if not candidate.is_absolute():
        candidate = (sections_dir / candidate).resolve()
    return candidate if candidate.exists() else None


def _row_duration(row: dict[str, object], video: Path | None) -> float:
    raw = row.get("duration")
    if isinstance(raw, (int, float)):
        return float(raw)
    return _ffprobe_duration(video) if video is not None else 0.0


def _is_main_section(type_str: str, *, is_first_in_scene: bool) -> bool:
    """Whether this section starts a new MAIN slide.

    The auto-created first section (``default.normal``, manim's default)
    counts as a main if it precedes any explicit ``simplex.*`` markers.
    """
    if type_str.startswith(_MAIN_PREFIX):
        return True
    return is_first_in_scene and type_str == _DEFAULT_NORMAL


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
            main_slides.append(
                MainSlide(
                    index=counter,
                    scene=scene,
                    name=_humanise(scene),
                    section_type="simplex.main",
                    subsections=(),
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
                    section_type="simplex.main",
                    subsections=(),
                )
            )
            counter += 1
            continue

        pending_name: str | None = None
        pending_type: str | None = None
        pending_subs: list[Subsection] = []

        for i, row in enumerate(rows):
            type_str = str(row.get("type", _DEFAULT_NORMAL))
            name = str(row.get("name", "unnamed"))
            video = _video_path(row, sections_dir)
            sub = Subsection(
                name=name,
                type_=type_str,
                video=video,
                duration_s=_row_duration(row, video),
            )
            if _is_main_section(type_str, is_first_in_scene=(i == 0)):
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
                pending_type = type_str if type_str.startswith(_MAIN_PREFIX) else "simplex.main"
                pending_subs = [sub]
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
