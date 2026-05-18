"""``make_chrome`` -- header / footer / page-number factory for ``BaseSlide``.

Replaces the old ``ContentSlide`` subclass with a composable factory:
authors call ``self.add_to_canvas(**make_chrome(theme, header=..., footer=...,
page=...))`` in their scene's ``setup()``. The chrome lives on the
manim-slides canvas so it survives ``clear_scene`` and ``Wipe``-style
transitions automatically.

``make_chrome`` returns a ``dict[str, Mobject]`` ready to splat into
``add_to_canvas``. It also shrinks ``scene.region`` to fit the chrome so
subsequent ``self.region.place(...)`` calls stay inside the body band.
"""

from typing import Any

from manim import Tex

from simplex.engine.region import Region
from simplex.theme.tokens import Theme


def make_chrome(
    theme: Theme,
    region: Region,
    *,
    header: str | None = None,
    footer: str | None = None,
    page: int | None = None,
) -> dict[str, Any]:
    """Build optional header/footer/page mobjects + shrink ``region`` for the body.

    Returns a mapping suitable for ``Slide.add_to_canvas(**...)``. Keys are
    ``"header"`` / ``"footer"`` / ``"page"``; entries absent when not requested.
    """
    chrome: dict[str, Any] = {}

    if header:
        head = Tex(header, font_size=theme.typography.h2)
        region.place(head, "top", buff=0.15)
        chrome["header"] = head
    if footer:
        foot = Tex(footer, font_size=theme.typography.caption)
        region.place(foot, "bottom-left", buff=0.2)
        chrome["footer"] = foot
    if page is not None:
        pg = Tex(str(page), font_size=theme.typography.caption)
        region.place(pg, "bottom-right", buff=0.2)
        chrome["page"] = pg

    region.shrink(
        top=theme.spacing.header_height if header else 0.0,
        bottom=theme.spacing.footer_height if (footer or page is not None) else 0.0,
    )
    return chrome
