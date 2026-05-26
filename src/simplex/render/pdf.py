"""Convert a rendered deck to PDF via ``manim_slides.convert.PDF`` in-process.

The PDF converter takes the per-scene ``PresentationConfig`` objects
written by manim-slides during render (under ``<output_dir>/slides/*.json``)
and writes one combined PDF. No subprocess, no shell.
"""

from pathlib import Path

from simplex.deck.config import DeckConfig
from simplex.render._warnings import filter_pydub_syntax_warning
from simplex.render.filenames import pdf_name


def export(deck: DeckConfig, *, output_dir: Path) -> Path:
    """Write ``<output_dir>/<title>-slides.pdf`` from rendered scenes."""
    filter_pydub_syntax_warning()
    from manim_slides.convert import PDF
    from manim_slides.present import get_scenes_presentation_config

    output_dir.mkdir(parents=True, exist_ok=True)
    media_dir = output_dir.resolve()
    pdf_path = media_dir / pdf_name(deck, "slides")
    scenes = deck.scene_class_names
    if not scenes:
        raise ValueError(f"deck {deck.slug!r} has no scenes/entrypoints configured")

    presentation_configs = get_scenes_presentation_config(
        list(scenes),
        media_dir / "slides",
    )
    PDF(presentation_configs=presentation_configs).convert_to(  # pyright: ignore[reportCallIssue]
        pdf_path
    )
    return pdf_path
