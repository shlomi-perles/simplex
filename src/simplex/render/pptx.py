"""Convert a rendered deck to PowerPoint via ``manim_slides.convert.PowerPoint``.

Free path through manim-slides' in-process converter; same pattern as
``render/pdf.py``. Users who need a corporate-PowerPoint format get it
without extra dependencies.
"""

from pathlib import Path

from simplex.deck.config import DeckConfig


def export(deck: DeckConfig, *, output_dir: Path) -> Path:
    """Write ``<output_dir>/<slug>.pptx`` from manim-slides' rendered scenes."""
    from manim_slides.convert import PowerPoint
    from manim_slides.present import get_scenes_presentation_config

    output_dir.mkdir(parents=True, exist_ok=True)
    media_dir = output_dir.resolve()
    pptx_path = media_dir / f"{deck.slug}.pptx"
    scenes = deck.scene_class_names
    if not scenes:
        raise ValueError(f"deck {deck.slug!r} has no scenes/entrypoints configured")

    presentation_configs = get_scenes_presentation_config(
        list(scenes),
        media_dir / "slides",
    )
    PowerPoint(presentation_configs=presentation_configs).convert_to(pptx_path)
    return pptx_path
