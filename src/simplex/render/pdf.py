"""Convert a rendered deck to PDF via `manim-slides convert`."""

import subprocess
from pathlib import Path

from simplex.deck.config import DeckConfig


def export(deck: DeckConfig, *, output_dir: Path) -> Path:
    """Write `<output_dir>/<slug>.pdf` from manim-slides' rendered scenes."""
    output_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = output_dir / f"{deck.slug}.pdf"
    scenes = deck.scene_class_names
    if not scenes:
        raise ValueError(f"deck {deck.slug!r} has no scenes/entrypoints configured")
    args: list[str] = [
        "manim-slides",
        "convert",
        "--to=pdf",
        *scenes,
        str(pdf_path),
    ]
    subprocess.run(args, check=True, cwd=deck.path)
    return pdf_path
