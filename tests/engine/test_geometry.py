"""Geometry helpers: frame center math, 3D arc, and surrounding-rect union."""

import pytest

np = pytest.importorskip("numpy")
pytest.importorskip("manim")

from manim import Square  # noqa: E402

from simplex.engine.geometry import (  # noqa: E402
    Arc3d,
    SurroundingRectangleUnion,
    get_frame_center,
    get_surrounding_rectangle,
)


def test_frame_center_defaults_to_origin() -> None:
    center = get_frame_center()
    assert abs(center[0]) < 1e-2
    assert abs(center[1]) < 1e-2


def test_frame_center_uses_explicit_coordinates() -> None:
    center = get_frame_center(
        left=np.array([-2.0, 0.0, 0.0]),
        right=np.array([2.0, 0.0, 0.0]),
        top=np.array([0.0, 1.0, 0.0]),
        bottom=np.array([0.0, -1.0, 0.0]),
    )
    assert center[0] == pytest.approx(0.0)
    assert center[1] == pytest.approx(0.0)


def test_arc3d_produces_segments_points() -> None:
    arc = Arc3d(
        np.array([1.0, 0.0, 0.0]),
        np.array([0.0, 1.0, 0.0]),
        np.array([0.0, 0.0, 0.0]),
        radius=1.0,
        segments=8,
    )
    # add_smooth_curve_to runs `segments` times, each adds 4 cubic-bezier control points.
    assert len(arc.points) > 0


def test_surrounding_rectangle_contains_diagonal_mobjects() -> None:
    a = Square(side_length=1.0).move_to((-2.0, -1.0, 0.0))
    b = Square(side_length=1.0).move_to((2.0, 1.0, 0.0))

    rect = get_surrounding_rectangle(a, b, buff=0.2)

    direction = b.get_center() - a.get_center()
    direction[2] = 0.0
    direction = direction / np.linalg.norm(direction)
    normal = np.array([-direction[1], direction[0], 0.0])
    mob_points = np.vstack((a.get_all_points(), b.get_all_points()))
    rect_points = rect.get_all_points()

    for axis in (direction, normal):
        mob_projection = mob_points @ axis
        rect_projection = rect_points @ axis
        assert rect_projection.min() <= mob_projection.min() - 0.19
        assert rect_projection.max() >= mob_projection.max() + 0.19


def test_surrounding_rectangle_union_overlap_yields_one_polygon() -> None:
    a = Square(side_length=1.0).move_to((0.0, 0.0, 0.0))
    b = Square(side_length=1.0).move_to((0.5, 0.0, 0.0))
    union = SurroundingRectangleUnion(a, b, buff=0.2)
    # Overlapping rects merge into one polygon.
    assert len(union) == 1


def test_surrounding_rectangle_union_disjoint_yields_two_polygons() -> None:
    a = Square(side_length=0.5).move_to((0.0, 0.0, 0.0))
    b = Square(side_length=0.5).move_to((5.0, 0.0, 0.0))
    union = SurroundingRectangleUnion(a, b, buff=0.05)
    assert len(union) == 2
