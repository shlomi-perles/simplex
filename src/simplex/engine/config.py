"""Mutate `manim.config` once per render from a Theme."""

from pathlib import Path

from simplex.theme.tokens import Theme


def configure_manim(
    theme: Theme,
    quality_key: str = "high_quality",
    *,
    media_dir: Path | None = None,
) -> None:
    """Apply theme + quality + media_dir to `manim.config`.

    `quality_key` must be one of `manim.constants.QUALITIES`. No custom enum.
    """
    from manim import config
    from manim.constants import QUALITIES

    if quality_key not in QUALITIES:
        known = ", ".join(sorted(QUALITIES))
        raise ValueError(f"unknown quality {quality_key!r}; known: {known}")

    config.background_color = theme.palette.background
    config.quality = quality_key
    config.tex_template = theme.latex.as_tex_template()
    if media_dir is not None:
        config.media_dir = str(media_dir)
