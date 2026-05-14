"""Geometry helpers: convex hull, surrounding rectangle, frame center.

The convex-hull helper requires SciPy -- install with
``pip install simplex[geometry]``. Everything else is numpy + Manim only.
"""

from typing import Any

import numpy as np
from manim import (
    DOWN,
    LEFT,
    RIGHT,
    UP,
    Mobject,
    Polygon,
    Rectangle,
    SurroundingRectangle,
    Text,
    VGroup,
    VMobject,
)


def get_convex_hull_polygon(
    points: np.ndarray,
    *,
    round_radius: float = 0.2,
    **kwargs: Any,
) -> Polygon:
    """Convex hull of 2D points (z is ignored) as a Manim `Polygon` with rounded corners.

    Requires SciPy.
    """
    try:
        from scipy.spatial import ConvexHull
    except ImportError as exc:
        msg = "get_convex_hull_polygon requires scipy. Install with: pip install simplex[geometry]"
        raise ImportError(msg) from exc

    hull = ConvexHull(points[:, :2])
    vertices = [np.append(points[i], 0) for i in hull.vertices]
    return Polygon(*vertices, **kwargs).round_corners(radius=round_radius)


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
        probe = Text(".").scale(0.01).to_edge(fallback_dir, buff=0)
        return getattr(probe, getter_name)()
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
