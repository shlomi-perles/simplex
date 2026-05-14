"""Invoke `manim-slides render` via subprocess.

The deck may use either layout:

- Package: ``decks/<slug>/slides/__init__.py`` re-exporting every scene. The
  runner ``cd``s into ``decks/<slug>/`` and invokes manim-slides against
  ``slides/__init__.py`` so relative imports inside the package work.
- Single-file legacy: ``decks/<slug>/slides.py``. The runner invokes
  manim-slides against that file directly.

manim-slides accepts bare scene class names regardless of source layout, so
we collapse ``module:Class`` entrypoints to their class names at the CLI.
"""

import subprocess
from pathlib import Path

from simplex.deck.config import DeckConfig

_QUALITY_FLAGS: dict[str, str] = {
    "low_quality": "l",
    "medium_quality": "m",
    "high_quality": "h",
    "production_quality": "p",
    "fourk_quality": "k",
    "example_quality": "e",
}


def _quality_flag(quality_key: str) -> str:
    if quality_key not in _QUALITY_FLAGS:
        known = ", ".join(sorted(_QUALITY_FLAGS))
        raise ValueError(f"unknown quality {quality_key!r}; known: {known}")
    return _QUALITY_FLAGS[quality_key]


def render(deck: DeckConfig, *, output_dir: Path) -> None:
    """Render every scene in `deck` into `output_dir` via manim-slides."""
    slides_path = deck.slides_path
    if not slides_path.exists():
        raise FileNotFoundError(
            f"deck {deck.slug!r} has neither slides/__init__.py nor slides.py at {deck.path}"
        )
    output_dir.mkdir(parents=True, exist_ok=True)
    scenes = deck.scene_class_names
    if not scenes:
        raise ValueError(f"deck {deck.slug!r} has no scenes/entrypoints configured")
    rel_slides = slides_path.relative_to(deck.path)
    args: list[str] = [
        "manim-slides",
        "render",
        "--quality",
        _quality_flag(deck.quality),
        "--media_dir",
        str(output_dir),
        str(rel_slides),
        *scenes,
    ]
    subprocess.run(args, check=True, cwd=deck.path)
