"""Geometry helpers: frame center math, convex hull when scipy is present."""

import pytest

np = pytest.importorskip("numpy")
pytest.importorskip("manim")

from simplex.engine.geometry import get_frame_center  # noqa: E402


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


def test_convex_hull_requires_scipy() -> None:
    pytest.importorskip("scipy")
    from simplex.engine.geometry import get_convex_hull_polygon

    pts = np.array(
        [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [1.0, 1.0, 0.0], [0.0, 1.0, 0.0], [0.5, 0.5, 0.0]],
    )
    poly = get_convex_hull_polygon(pts)
    assert poly is not None
