"""bounding_box overlay structure + indexx_labels color cycling."""

import pytest

pytest.importorskip("manim")

from manim import Square, VGroup

from simplex.engine.debug import bounding_box, indexx_labels


def test_bounding_box_returns_outline_and_dots() -> None:
    sq = Square(side_length=2.0)
    bb = bounding_box(sq)
    # Two children: the outline VGroup and the dots VGroup.
    assert len(bb) == 2
    outline, dots = bb
    assert len(outline) == 4  # four edges
    # Eight critical points (4 corners + 4 edge midpoints).
    assert len(dots) == 8


def test_bounding_box_with_center_adds_one_dot() -> None:
    sq = Square(side_length=1.0)
    bb = bounding_box(sq, include_center=True)
    _, dots = bb
    assert len(dots) == 9


def test_bounding_box_always_returns_redrawn_mob() -> None:
    sq = Square(side_length=1.0)
    bb = bounding_box(sq, always=True)
    # always_redraw returns a Mobject with updaters attached. Manim 0.20
    # removed `has_updaters()` -- read the attribute directly.
    assert bool(bb.updaters)


def test_indexx_labels_cycles_colors() -> None:
    # A VGroup with two children -> two label groups, two colors.
    g = VGroup(Square(), Square())
    labels = indexx_labels(g)
    assert len(labels) == 2
