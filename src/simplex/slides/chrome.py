"""``make_chrome`` -- header / footer factory for ``BaseSlide``.

Authors call ``self.add_to_canvas(**chrome.mobjects)`` in their scene's
``setup()`` and re-bind ``self.region = chrome.body_region``. The chrome
lives on the manim-slides canvas so it survives ``clear_scene`` and
``Wipe``-style transitions automatically.

``make_chrome`` is a *pure* factory: it doesn't mutate its ``region``
argument. It returns a :class:`Chrome` ``NamedTuple`` carrying both the
mobjects for the canvas and a fresh, shrunk ``Region`` for the body.

The actual buff distances (header gap, footer gap) live in
``Theme.spacing`` so themes can tune them deck-wide. Slide numbering and
clock are presentation chrome, not rendered chrome — they live in the
RevealJS template / web settings (see ``simplex.web``).
"""

from typing import Any, NamedTuple

from manim import DL, UP, Tex

from simplex.engine.region import Region
from simplex.theme.tokens import Theme


class Chrome(NamedTuple):
    """Result of :func:`make_chrome`.

    ``mobjects`` -- dict ready to splat into ``Slide.add_to_canvas(**...)``.
    ``body_region`` -- a *new* ``Region`` shrunk to the body band; the
    original argument is left untouched.
    """

    mobjects: dict[str, Any]
    body_region: Region


def make_chrome(
    theme: Theme,
    region: Region,
    *,
    header: str | None = None,
    footer: str | None = None,
) -> Chrome:
    """Build optional header/footer mobjects and return a shrunk body Region.

    The ``region`` argument is **not** mutated. The returned
    ``Chrome.body_region`` is a fresh Region shrunk to fit beneath the
    requested chrome elements. Buff distances come from ``theme.spacing``
    (``header_buff``, ``footer_buff``).
    """
    mobs: dict[str, Any] = {}

    if header:
        head = Tex(header, font_size=theme.typography.h2)
        region.place(head, UP, buff=theme.spacing.header_buff)
        mobs["header"] = head
    if footer:
        foot = Tex(footer, font_size=theme.typography.caption)
        region.place(foot, DL, buff=theme.spacing.footer_buff)
        mobs["footer"] = foot

    body = Region(
        top=region.top - (theme.spacing.header_height if header else 0.0),
        bottom=region.bottom + (theme.spacing.footer_height if footer else 0.0),
        left=region.left,
        right=region.right,
    )
    return Chrome(mobjects=mobs, body_region=body)
