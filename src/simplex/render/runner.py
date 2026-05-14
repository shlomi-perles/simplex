"""Invoke `manim-slides render` via subprocess."""

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
    slides_py = deck.path / "slides.py"
    output_dir.mkdir(parents=True, exist_ok=True)
    args: list[str] = [
        "manim-slides",
        "render",
        "--quality",
        _quality_flag(deck.quality),
        "--output_dir",
        str(output_dir),
        str(slides_py),
        *deck.scenes,
    ]
    subprocess.run(args, check=True)
