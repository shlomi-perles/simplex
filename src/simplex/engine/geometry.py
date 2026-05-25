"""Geometry helpers: convex hull, surrounding rectangle, frame center.

Also exports `Arc3d`, `SurroundingRectangleUnion`, and `Vcis` -- small
geometry primitives that don't have a clean Manim equivalent (Manim's
`ArcBetweenPoints` is 2D-only, and `SurroundingRectangle` doesn't merge
with neighbours).
"""

from copy import deepcopy
from typing import Any

import numpy as np
from manim import (
    DOWN,
    LEFT,
    RIGHT,
    UP,
    ConvexHull,
    Mobject,
    Polygon,
    Rectangle,
    SurroundingRectangle,
    Union,
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
    flat = _outer_hull_points(points)
    hull = ConvexHull(*flat, **kwargs)
    hull.round_corners(radius=round_radius)
    return hull


def _outer_hull_points(points: np.ndarray) -> list[tuple[float, float, float]]:
    """Return outer 2D hull vertices in stable order, discarding interior points."""
    pts = sorted({(float(p[0]), float(p[1])) for p in points})
    if len(pts) <= 1:
        return [(x, y, 0.0) for x, y in pts]

    def cross(
        origin: tuple[float, float],
        a: tuple[float, float],
        b: tuple[float, float],
    ) -> float:
        return (a[0] - origin[0]) * (b[1] - origin[1]) - (a[1] - origin[1]) * (b[0] - origin[0])

    lower: list[tuple[float, float]] = []
    for pt in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], pt) <= 0:
            lower.pop()
        lower.append(pt)

    upper: list[tuple[float, float]] = []
    for pt in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], pt) <= 0:
            upper.pop()
        upper.append(pt)

    hull = lower[:-1] + upper[:-1]
    return [(x, y, 0.0) for x, y in hull]


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


def Vcis(theta: float, *, clockwise: bool = False) -> np.ndarray:  # noqa: N802 -- math idiom
    """Unit vector at angle `theta` (radians).

    Default convention: counter-clockwise from +x. With `clockwise=True`,
    measured clockwise from +y -- handy for clock-face layouts.
    """
    if clockwise:
        return np.sin(theta) * RIGHT + np.cos(theta) * UP
    return np.cos(theta) * RIGHT + np.sin(theta) * UP


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
        start = center + _normalize(a - center) * radius
        end = center + _normalize(b - center) * radius
        self.set_points([start])
        for t in np.linspace(0.0, 1.0, segments, endpoint=True):
            chord_pt = start + t * (end - start)
            self.add_smooth_curve_to(center + _normalize(chord_pt - center) * radius)


def _normalize(v: np.ndarray) -> np.ndarray:
    norm = float(np.linalg.norm(v))
    return v / norm if norm > 0 else v


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
        beziers = [union.points[i : i + 4] for i in range(0, len(union.points), 4)]

        polygons: list[list[np.ndarray]] = []
        current: list[np.ndarray] = []
        for bez in beziers:
            first = np.asarray(bez[0], dtype=float)
            last = np.asarray(bez[-1], dtype=float)
            if not current:
                current.append(first)
            elif np.allclose(last, current[0]):
                current.append(first)
                polygons.append(current)
                current = []
            else:
                current.append(first)
        self._polygons = polygons

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
                edge_a = _normalize(vertex - poly[(i - 1) % len(poly)])
                edge_b = _normalize(vertex - poly[(i + 1) % len(poly)])
                bisector = edge_a + edge_b
                cross_z = float(np.cross(edge_a[:2], edge_b[:2]))
                if cross_z > 0:
                    self._polygons[j][i] = vertex + unbuff * bisector
                else:
                    self._polygons[j][i] = vertex - unbuff * bisector
