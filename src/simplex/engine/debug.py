"""Debug-time visualisations: bounding box, multi-color glyph indices.

Manim ships a single-color `index_labels`; `indexx_labels` walks one extra
level of submobject nesting and rotates through colors so multi-string
`MathTex` becomes legible without manual coloring.

`bounding_box` returns a debug overlay (corner + edge dots, faint outline)
useful when tuning `next_to` / alignment.
"""

from typing import Any, cast

import numpy as np
from manim import (
    BLUE_D,
    DOWN,
    GREEN_D,
    ORANGE,
    PURPLE,
    RED_B,
    RED_D,
    YELLOW,
    Dot,
    Line,
    Mobject,
    MoveAlongPath,
    Text,
    VGroup,
    always_redraw,
    index_labels,
    turn_animation_into_updater,
)
from manim.utils.color import ParsableManimColor

_RAINBOW: tuple[ParsableManimColor, ...] = (RED_D, ORANGE, YELLOW, GREEN_D, BLUE_D, PURPLE)


def bounding_box(
    mobject: Mobject,
    *,
    always: bool = False,
    include_center: bool = False,
) -> VGroup:
    """A small debug overlay showing the eight critical points of `mobject`.

    Pass `always=True` to wrap the result in `always_redraw` so the overlay
    follows the mobject through animations. Set `include_center=True` to
    add a dot at the bounding-box center.
    """
    if always:
        return cast(
            VGroup,
            always_redraw(
                lambda: bounding_box(mobject, always=False, include_center=include_center)
            ),
        )

    from manim import DL, DR, LEFT, ORIGIN, RIGHT, UL, UP, UR

    size = min(mobject.get_width(), mobject.get_height())
    dot_radius = float(np.clip(size / 12, 0.02, 0.06))
    corners = [
        Dot(mobject.get_critical_point(direction), radius=dot_radius, color=GREEN_D)
        for direction in (UL, UR, DR, DL)
    ]
    edges_dots = [
        Dot(mobject.get_critical_point(direction), radius=dot_radius, color=RED_B)
        for direction in (LEFT, RIGHT, UP, DOWN)
    ]
    extras = []
    if include_center:
        extras.append(Dot(mobject.get_critical_point(ORIGIN), radius=dot_radius, color=BLUE_D))
    outline = VGroup(
        *(
            Line(
                corners[i].get_center(),
                corners[(i + 1) % 4].get_center(),
                stroke_width=2,
                stroke_opacity=0.5,
            )
            for i in range(4)
        )
    )
    return VGroup(outline, VGroup(*corners, *edges_dots, *extras))


def indexx_labels(
    mobject: Mobject,
    *,
    colors: tuple[ParsableManimColor, ...] = _RAINBOW,
    label_height: float | None = None,
    **kwargs: Any,
) -> VGroup:
    """Color-cycling, two-level wrapper around `manim.index_labels`.

    Useful when `mobject` is a multi-string `MathTex`: each top-level
    submobject's glyph indices get their own color so a long label like
    `MathTex("\\sin", "(", "x", ")")` becomes visually parseable.
    """
    computed_label_height = (
        max(mobject.get_height() / 8, 0.18) if label_height is None else label_height
    )
    return VGroup(
        *(
            index_labels(
                mobject[i],
                color=colors[i % len(colors)],
                label_height=computed_label_height,
                **kwargs,
            )
            for i in range(len(mobject.submobjects))
        )
    )


def debug_glyph(
    scene: Any,
    glyph: Any,
    *,
    writing_dot: bool = True,
    writing_cycle_length: float = 5.0,
    writing_dot_color: str = "#4080FF",
    show_dot_count: bool = False,
    dot_count_direction: np.ndarray = DOWN,
) -> None:
    """Reduce a glyph to a faint outline + one dot per anchor point.

    Useful for inspecting why a glyph aligns oddly: every cubic-bezier
    anchor (the points the glyph actually passes through) becomes a Dot;
    even-indexed dots are green / half-opacity, odd-indexed are red /
    quarter-opacity.

    The original MF_Tools helper iterated `mobject.data` (an OpenGL-only
    layout). On Manim CE / cairo we read `glyph.points[::4]` -- i.e. the
    start anchors of each cubic, which is the cairo analogue. The
    `writing_dot` (a `Dot` traveling along the glyph's path on a loop
    via `turn_animation_into_updater`) replaces the OpenGL-only `GlowDot`.

    `show_dot_count` adds a `Text` count next to the glyph.
    """
    base_size = max(glyph.get_width(), glyph.get_height())
    radius = 0.01 * base_size
    anchors = glyph.points[::4] if len(glyph.points) else glyph.points
    dots = VGroup(*(Dot(point, radius=radius) for point in anchors))
    if len(dots):
        dots[::2].set_opacity(0.5).set_color(GREEN_D)
        dots[1::2].set_opacity(0.25).set_color(RED_D)
    glyph.set_opacity(0.1)
    scene.add(dots)
    glyph.data_dots = dots

    if writing_dot and len(glyph.points):
        cursor = Dot(color=writing_dot_color, radius=0.06 * base_size)
        scene.add(cursor)
        turn_animation_into_updater(
            MoveAlongPath(cursor, glyph, run_time=writing_cycle_length),
            cycle=True,
        )
        glyph.writing_dot = cursor

    if show_dot_count:
        label = Text(f"Data points: {len(dots)}")
        label.scale(max(0.1, glyph.get_width() / max(label.get_width(), 1e-6)))
        label.next_to(glyph, dot_count_direction, buff=glyph.get_height() / 4)
        scene.add(label)
        glyph.dot_count = label


def debug_glyphs(scene: Any, *mobjects: Mobject, **kwargs: Any) -> None:
    """Run `debug_glyph` over every glyph of every mobject."""
    for parent in mobjects:
        for glyph in parent:
            debug_glyph(scene, glyph, **kwargs)


__all__ = [
    "bounding_box",
    "debug_glyph",
    "debug_glyphs",
    "indexx_labels",
]
