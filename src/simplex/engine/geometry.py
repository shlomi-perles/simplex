"""Geometry helpers: convex hull, surrounding rectangle, frame center."""

from typing import Any

import numpy as np
from manim import (
    DOWN,
    LEFT,
    RIGHT,
    UP,
    ConvexHull,
    Mobject,
    Rectangle,
    SurroundingRectangle,
    VGroup,
    VMobject,
    config,
)


def get_convex_hull_polygon(
    points: np.ndarray,
    *,
    round_radius: float = 0.2,
    **kwargs: Any,
) -> ConvexHull:
    """Convex hull of 2D points (z is ignored) with rounded corners.

    Uses Manim's built-in :class:`~.ConvexHull` (added in 0.19.0), so no scipy.
    """
    flat = [(float(p[0]), float(p[1]), 0.0) for p in points]
    hull = ConvexHull(*flat, **kwargs)
    hull.round_corners(radius=round_radius)
    return hull


def get_surrounding_rectangle(
    a: VMobject,
    b: VMobject,
    **kwargs: Any,
) -> Rectangle:
    """A rotated `SurroundingRectangle` whose long edge spans the segment a -> b."""
    rect_height = float(np.linalg.norm(a.get_center() - b.get_center()))
    b_aligned = b.copy().match_x(a)
    rect = SurroundingRectangle(VGroup(a, b_aligned), **kwargs).scale_to_fit_height(rect_height)
    angle = np.arctan2(
        a.get_center()[1] - b.get_center()[1],
        a.get_center()[0] - b.get_center()[0],
    )
    rect.rotate(angle, about_point=a.get_center())
    return rect


def _edge_point(
    obj: Mobject | np.ndarray | None,
    fallback_dir: np.ndarray,
    getter_name: str,
) -> np.ndarray:
    if obj is None:
        half_w = config.frame_width / 2
        half_h = config.frame_height / 2
        # Manim getters return the *outer* edge of the mobject in that
        # direction. For the frame, the analogous point is the frame edge
        # opposite to `fallback_dir` (the edge facing inwards).
        if np.array_equal(fallback_dir, LEFT):
            return np.array([-half_w, 0.0, 0.0])
        if np.array_equal(fallback_dir, RIGHT):
            return np.array([half_w, 0.0, 0.0])
        if np.array_equal(fallback_dir, UP):
            return np.array([0.0, half_h, 0.0])
        if np.array_equal(fallback_dir, DOWN):
            return np.array([0.0, -half_h, 0.0])
        return np.array([0.0, 0.0, 0.0])
    if isinstance(obj, Mobject):
        return getattr(obj, getter_name)()
    return np.asarray(obj, dtype=float)


def get_frame_center(
    *,
    left: Mobject | np.ndarray | None = None,
    right: Mobject | np.ndarray | None = None,
    top: Mobject | np.ndarray | None = None,
    bottom: Mobject | np.ndarray | None = None,
) -> np.ndarray:
    """Center of the rectangle defined by the four edges.

    Each edge may be:
      - a `Mobject` (its inner edge facing the rectangle is used),
      - a 3-vector point, or
      - `None` (falls back to the screen edge in that direction).
    """
    left_pt = _edge_point(left, LEFT, "get_right")
    right_pt = _edge_point(right, RIGHT, "get_left")
    top_pt = _edge_point(top, UP, "get_bottom")
    bottom_pt = _edge_point(bottom, DOWN, "get_top")
    return np.array(
        [
            (left_pt[0] + right_pt[0]) / 2,
            (top_pt[1] + bottom_pt[1]) / 2,
            0.0,
        ]
    )
