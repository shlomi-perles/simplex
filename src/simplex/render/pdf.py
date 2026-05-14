"""Convert a rendered deck to PDF via `manim-slides convert`."""

import subprocess
from pathlib import Path

from simplex.deck.config import DeckConfig


def export(deck: DeckConfig, *, output_dir: Path) -> Path:
    pdf_path = output_dir / f"{deck.slug}.pdf"
    args: list[str] = [
        "manim-slides",
        "convert",
        "--to=pdf",
        *deck.scenes,
        str(pdf_path),
    ]
    subprocess.run(args, check=True)
    return pdf_path
