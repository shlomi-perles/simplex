"""Shared visual chrome for the showcase deck."""

from typing import Any

from manim import BOLD, UP, Text, Title

from simplex.engine.scaling import scale_to_fit

SIMPLEX_LOGO = Text("Simplex", font="Space Grotesk", weight=BOLD, font_size=24)
_SHOWCASE_TITLE_FONT_SIZE = 24


def setup_showcase_chrome(slide: Any, title: str) -> None:
    """Install the Simplex logo footer and reserve a top title band."""
    slide.setup_chrome(footer=SIMPLEX_LOGO.copy())
    showcase_title = Title(
        title,
        font_size=_SHOWCASE_TITLE_FONT_SIZE,
        underline_buff=0.12,
    )
    scale_to_fit(showcase_title, len_x=slide.region.width, buff=0.25, max_scale=1.0)
    slide.region.place(showcase_title, UP, buff=0.12)
    fix_in_frame = getattr(showcase_title, "fix_in_frame", None)
    if callable(fix_in_frame):
        fix_in_frame()
    slide.region.update(top=showcase_title)
    slide.showcase_title = showcase_title
