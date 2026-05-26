"""Geometry helpers: surrounding rectangle, frame center, 3D arc, unioned rect.

Manim 0.20.x already ships :class:`~.ConvexHull` (QuickHull) and
:func:`~.manim.utils.space_ops.normalize`/``angle_of_vector`` -- callers
should import those directly instead of any Simplex wrapper. This module
sticks to additions that Manim does not provide:

- :class:`Arc3d` -- arc on a sphere; Manim's ``ArcBetweenPoints`` is 2D.
- :class:`SurroundingRectangleUnion` -- merged surrounding rect for groups.
- :func:`get_surrounding_rectangle` -- rotated rect spanning two mobjects.
- :func:`get_frame_center` -- midpoint of four mobject/point/edge anchors.
"""

from copy import deepcopy
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
    Union,
    VGroup,
    VMobject,
    config,
)
from manim.utils.space_ops import angle_of_vector, normalize


def get_surrounding_rectangle(
    a: VMobject,
    b: VMobject,
    **kwargs: Any,
) -> Rectangle:
    """A rotated `SurroundingRectangle` whose long edge spans the segment a -> b."""
    rect_height = float(np.linalg.norm(a.get_center() - b.get_center()))
    b_aligned = b.copy().match_x(a)
    rect = SurroundingRectangle(VGroup(a, b_aligned), **kwargs).scale_to_fit_height(rect_height)
    angle = angle_of_vector(a.get_center() - b.get_center())
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


class Arc3d(VMobject):
    """A 3D arc spanning from `a` to `b` along a fixed-radius sphere about `center`.

    Manim's `ArcBetweenPoints` is implicitly 2D. This walks the chord in
    `segments` steps and projects each sample back onto the sphere of the
    given radius -- credit to @uwezi (Manim Discord).
    """

    def __init__(
        self,
        a: np.ndarray,
        b: np.ndarray,
        center: np.ndarray,
        *,
        radius: float = 1.0,
        segments: int = 40,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        a = np.asarray(a, dtype=float)
        b = np.asarray(b, dtype=float)
        center = np.asarray(center, dtype=float)
        start = center + normalize(a - center) * radius
        end = center + normalize(b - center) * radius
        self.set_points([start])
        for t in np.linspace(0.0, 1.0, segments, endpoint=True):
            chord_pt = start + t * (end - start)
            self.add_smooth_curve_to(center + normalize(chord_pt - center) * radius)


class SurroundingRectangleUnion(VGroup):
    """One or more polygons that together surround all `mobjects`.

    Build a `SurroundingRectangle` per mobject, union them with Manim's
    boolean op, optionally pull edges inward by `unbuff` (so adjacent
    `SurroundingRectangleUnion`s for different groups don't touch), and
    round corners by `corner_radius`.

    Result: a `VGroup` of `Polygon` mobjects -- one per connected region
    after the union.
    """

    def __init__(
        self,
        *mobjects: Mobject,
        buff: float = 0.1,
        unbuff: float = 0.05,
        corner_radius: float = 0.0,
        **kwargs: Any,
    ) -> None:
        rects = VGroup(*(SurroundingRectangle(m, buff=buff) for m in mobjects))
        union = Union(*rects, **kwargs) if len(rects) > 1 else rects[0]

        # Manim's ``Union`` is itself a VMobject; ``get_subpaths`` splits its
        # control-point array into one connected component per polygon, and
        # the start anchor of each cubic curve inside a subpath is one of
        # the polygon's corners. This replaces the hand-rolled ``points[i:i+4]``
        # walk that used to do the same job.
        nppcc = union.n_points_per_cubic_curve
        self._polygons: list[list[np.ndarray]] = [
            [np.asarray(p, dtype=float) for p in subpath[::nppcc]]
            for subpath in union.get_subpaths()
        ]

        if unbuff > 0:
            self._apply_unbuff(unbuff)
        super().__init__(*(Polygon(*poly, **kwargs) for poly in self._polygons), **kwargs)
        if corner_radius > 0:
            for poly in self:
                poly.round_corners(corner_radius)

    def _apply_unbuff(self, unbuff: float) -> None:
        original = deepcopy(self._polygons)
        for j, poly in enumerate(original):
            for i, vertex in enumerate(poly):
                edge_a = normalize(vertex - poly[(i - 1) % len(poly)])
                edge_b = normalize(vertex - poly[(i + 1) % len(poly)])
                bisector = edge_a + edge_b
                cross_z = float(np.cross(edge_a[:2], edge_b[:2]))
                if cross_z > 0:
                    self._polygons[j][i] = vertex + unbuff * bisector
                else:
                    self._polygons[j][i] = vertex - unbuff * bisector
