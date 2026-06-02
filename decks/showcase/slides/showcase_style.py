"""Shared visual chrome for the showcase deck."""

from typing import Any

from manim import BOLD, UP, Text, Title

SIMPLEX_LOGO = Text("Simplex", font="Space Grotesk", weight=BOLD)


def setup_showcase_chrome(slide: Any, title: str) -> None:
    """Install the Simplex logo footer and reserve a top title band."""
    slide.setup_chrome(footer=SIMPLEX_LOGO.copy())
    showcase_title = Title(title)
    slide.region.place(showcase_title, UP)
    fix_in_frame = getattr(showcase_title, "fix_in_frame", None)
    if callable(fix_in_frame):
        fix_in_frame()
    slide.region.update(top=showcase_title)
    slide.add_to_canvas(showcase_title=showcase_title)
