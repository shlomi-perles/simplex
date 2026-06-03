"""Shared visual chrome for the showcase deck."""

from collections.abc import Iterable
from typing import Any

from manim import BOLD, UP, Text, Title

SIMPLEX_LOGO = Text("Simplex", font="Space Grotesk", weight=BOLD)

_TITLE_TEX_REPLACEMENTS = {
    "\\": r"\textbackslash{}",
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
}


def _escape_title_tex(text: str) -> str:
    return "".join(_TITLE_TEX_REPLACEMENTS.get(char, char) for char in text)


def _install_footer_preserving_clear_scene(slide: Any, footer: Any) -> None:
    original_clear_scene = slide.clear_scene

    def clear_scene_with_showcase_footer(*, exclude: Iterable[Any] = ()) -> None:
        original_clear_scene(exclude=(*exclude, footer))

    slide.clear_scene = clear_scene_with_showcase_footer


def setup_showcase_chrome(slide: Any, title: str) -> None:
    """Install the Simplex logo footer and reserve a top title band."""
    chrome = slide.setup_chrome(footer=SIMPLEX_LOGO.copy())
    if chrome is not None and "footer" in chrome.mobjects:
        _install_footer_preserving_clear_scene(slide, chrome.mobjects["footer"])
    showcase_title = Title(_escape_title_tex(title))
    slide.region.place(showcase_title, UP)
    fix_in_frame = getattr(showcase_title, "fix_in_frame", None)
    if callable(fix_in_frame):
        fix_in_frame()
    slide.region.update(top=showcase_title)
    slide.add_to_canvas(showcase_title=showcase_title)
