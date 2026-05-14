"""Parse manim-slides per-scene PresentationConfig JSON files into SlideRefs.

manim-slides writes one JSON file per rendered scene under the ``slides/``
subtree of its ``--media_dir``. The exact layout has shifted across releases;
we keep our parser permissive (extra fields ignored, missing fields tolerated)
so a minor upstream bump does not break the builder.

If no JSON files are found (e.g. an unrendered test build) the manifest
falls back to a synthetic ``SlideRef`` per declared scene with no video.
"""

import contextlib
import json
import shutil
import subprocess
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from simplex.deck.config import DeckConfig


class SlideRef(BaseModel):
    """One slide as it appears in the sidebar / shared between viewer + parent."""

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)
    index: int
    scene: str
    title: str | None = None
    duration_s: float = 0.0
    video_paths: tuple[Path, ...] = ()
    thumbnail: Path | None = None
    notes: str | None = None


class DeckManifest(BaseModel):
    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)
    deck_slug: str
    slides: tuple[SlideRef, ...]

    @property
    def slide_count(self) -> int:
        return len(self.slides)

    @property
    def total_duration_s(self) -> float:
        return sum(s.duration_s for s in self.slides)


def _ffprobe_duration(video: Path) -> float:
    """Return the duration of `video` in seconds, or 0.0 if ffprobe is missing."""
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


def _scene_json_paths(media_dir: Path, scenes: tuple[str, ...]) -> list[Path]:
    """Locate the per-scene JSON in `media_dir`, preserving declared scene order."""
    candidates: dict[str, Path] = {}
    for path in media_dir.rglob("*.json"):
        # PresentationConfig files manim-slides emits live under .../slides/.
        if "slides" not in path.parts:
            continue
        candidates[path.stem] = path
    return [candidates[s] for s in scenes if s in candidates]


def _slides_from_scene_json(scene_json: Path, scene_name: str) -> list[dict[str, object]]:
    """Return the list of slide segments, tolerating schema drift."""
    try:
        raw_text = scene_json.read_text(encoding="utf-8")
    except OSError:
        return []
    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError:
        return []
    raw = data.get("slides") if isinstance(data, dict) else None
    if not isinstance(raw, list):
        return []
    rows: list[dict[str, object]] = []
    for entry in raw:
        if isinstance(entry, dict):
            row = dict(entry)
            row.setdefault("_scene", scene_name)
            rows.append(row)
    return rows


def _resolve_video(scene_json: Path, entry: dict[str, object]) -> Path | None:
    raw = entry.get("file") or entry.get("video") or entry.get("path")
    if not isinstance(raw, str) or not raw:
        return None
    candidate = Path(raw)
    if not candidate.is_absolute():
        candidate = (scene_json.parent / candidate).resolve()
    return candidate if candidate.exists() else None


def build_manifest(
    deck: DeckConfig,
    *,
    media_dir: Path,
) -> DeckManifest:
    """Read manim-slides JSON for `deck`; degrade gracefully when absent."""
    scenes = deck.scene_class_names
    json_paths = _scene_json_paths(media_dir, scenes) if media_dir.exists() else []

    if not json_paths:
        synthetic = tuple(
            SlideRef(index=i, scene=name, title=_humanise(name)) for i, name in enumerate(scenes)
        )
        return DeckManifest(deck_slug=deck.slug, slides=synthetic)

    slides: list[SlideRef] = []
    global_index = 0
    for scene_json in json_paths:
        scene = scene_json.stem
        rows = _slides_from_scene_json(scene_json, scene)
        if not rows:
            slides.append(SlideRef(index=global_index, scene=scene, title=_humanise(scene)))
            global_index += 1
            continue
        for sub_idx, entry in enumerate(rows):
            video = _resolve_video(scene_json, entry)
            duration = _ffprobe_duration(video) if video is not None else 0.0
            title = entry.get("title")
            if not isinstance(title, str):
                title = _humanise(scene) if sub_idx == 0 else None
            notes = entry.get("notes")
            slides.append(
                SlideRef(
                    index=global_index,
                    scene=scene,
                    title=title,
                    duration_s=duration,
                    video_paths=(video,) if video is not None else (),
                    notes=notes if isinstance(notes, str) else None,
                )
            )
            global_index += 1

    return DeckManifest(deck_slug=deck.slug, slides=tuple(slides))


def _humanise(camel: str) -> str:
    """Convert ``CamelCase`` into ``Camel Case`` for sidebar titles."""
    if not camel:
        return camel
    out: list[str] = [camel[0]]
    for ch in camel[1:]:
        if ch.isupper() and out[-1] != " ":
            out.append(" ")
        out.append(ch)
    return "".join(out)
