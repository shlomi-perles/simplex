"""Region -- mutable rectangular sub-area of the frame.

The region API speaks in Manim's direction vectors (``UP``, ``DR``, ``ORIGIN``,
…) rather than ad-hoc strings. Each direction's ``(x, y)`` components in
``{-1, 0, 1}`` pick the corresponding edge / midpoint / center of the region.
"""

from collections.abc import Iterable
from numbers import Real
from typing import Self

import numpy as np
from manim import Mobject
from pydantic import BaseModel, ConfigDict, ValidationInfo, field_validator

type EdgeValue = float | np.ndarray | Iterable[float] | Mobject

_EDGE_SPECS = {
    "top": (1, "get_bottom"),
    "bottom": (1, "get_top"),
    "left": (0, "get_right"),
    "right": (0, "get_left"),
}


def _as_dir(anchor: np.ndarray | Iterable[float]) -> np.ndarray:
    """Coerce ``anchor`` to a length-3 float vector with components in {-1, 0, 1}.

    Raises ``ValueError`` for non-cardinal vectors so callers fail fast instead
    of getting a silently wrong placement.
    """
    arr = np.asarray(anchor, dtype=float)
    if arr.shape == (2,):
        arr = np.append(arr, 0.0)
    if arr.shape != (3,):
        raise ValueError(f"anchor must be a 2D or 3D direction vector, got shape {arr.shape}")
    if not np.all(np.isin(np.sign(arr).astype(int), (-1, 0, 1))):
        raise ValueError(
            f"anchor components must be in {{-1, 0, 1}} (a Manim direction); got {arr.tolist()}"
        )
    return np.sign(arr)


def _edge_coordinate(value: EdgeValue, axis: int, getter_name: str) -> float:
    if isinstance(value, Mobject):
        value = getattr(value, getter_name)()
    if isinstance(value, Real):
        return float(value)

    point = np.asarray(value, dtype=float)
    if point.shape != (3,):
        raise ValueError(f"edge point must be a 3D point, got shape {point.shape}")
    return float(point[axis])


def _edge_value(edge: str, value: EdgeValue) -> float:
    axis, getter_name = _EDGE_SPECS[edge]
    return _edge_coordinate(value, axis, getter_name)


class Region(BaseModel):
    """A mutable axis-aligned region in Manim frame coordinates."""

    model_config = ConfigDict(arbitrary_types_allowed=True)
    top: float
    bottom: float
    left: float
    right: float

    @field_validator("top", "bottom", "left", "right", mode="before")
    @classmethod
    def _coerce_edge_value(cls, value: EdgeValue, info: ValidationInfo) -> float:
        if info.field_name is None:
            raise ValueError("edge field name is missing")
        return _edge_value(info.field_name, value)

    def __init__(
        self,
        *,
        top: EdgeValue,
        bottom: EdgeValue,
        left: EdgeValue,
        right: EdgeValue,
    ) -> None:
        super().__init__(top=top, bottom=bottom, left=left, right=right)

    @classmethod
    def full_frame(cls) -> Self:
        from manim import config

        half_w = config.frame_width / 2
        half_h = config.frame_height / 2
        return cls(top=half_h, bottom=-half_h, left=-half_w, right=half_w)

    @property
    def width(self) -> float:
        return self.right - self.left

    @property
    def height(self) -> float:
        return self.top - self.bottom

    @property
    def center(self) -> np.ndarray:
        cx = (self.left + self.right) / 2
        cy = (self.top + self.bottom) / 2
        return np.array([cx, cy, 0.0])

    def _anchor_point(self, direction: np.ndarray) -> np.ndarray:
        """Map a normalized direction vector to the matching point of this region."""
        cx, cy, _ = self.center
        x = self.left if direction[0] < 0 else (self.right if direction[0] > 0 else cx)
        y = self.bottom if direction[1] < 0 else (self.top if direction[1] > 0 else cy)
        return np.array([x, y, 0.0])

    def place(
        self,
        mob: Mobject,
        anchor: np.ndarray | Iterable[float] | None = None,
        buff: float = 0.0,
    ) -> Mobject:
        """Move ``mob`` so its anchor sits at the matching point of this region.

        ``anchor`` is a Manim direction vector (``UP``, ``DR``, ``ORIGIN``, …).
        ``buff`` pulls ``mob`` inward by that distance plus half its own size
        along the same axis, so a non-zero ``buff`` always leaves visible
        breathing room between the mob and the region edge.
        """
        from manim import ORIGIN

        direction = _as_dir(ORIGIN if anchor is None else anchor)
        mob.move_to(self._anchor_point(direction))
        half_w, half_h = mob.width / 2, mob.height / 2
        dx = -direction[0] * (buff + half_w)
        dy = -direction[1] * (buff + half_h)
        if dx or dy:
            mob.shift(np.array([dx, dy, 0.0]))
        return mob

    def update(
        self,
        *,
        top: EdgeValue | None = None,
        bottom: EdgeValue | None = None,
        left: EdgeValue | None = None,
        right: EdgeValue | None = None,
    ) -> None:
        """Update region edges from floats, points, or neighbouring mobjects.

        Point values contribute their relevant coordinate: x for left/right,
        y for top/bottom. Mobjects contribute the edge facing this region, then
        use the same coordinate rule.
        """
        updates = (("top", top), ("bottom", bottom), ("left", left), ("right", right))
        for edge, value in updates:
            if value is not None:
                setattr(self, edge, _edge_value(edge, value))

    def shrink(
        self,
        *,
        top: float = 0.0,
        bottom: float = 0.0,
        left: float = 0.0,
        right: float = 0.0,
    ) -> None:
        self.top -= top
        self.bottom += bottom
        self.left += left
        self.right -= right

    def reset(self) -> None:
        full = Region.full_frame()
        self.top = full.top
        self.bottom = full.bottom
        self.left = full.left
        self.right = full.right

    def split(
        self,
        axis: np.ndarray | Iterable[float],
        k: int,
    ) -> list["Region"]:
        """Split this region into ``k`` sub-regions strung along ``axis``.

        Returns sub-regions in the direction of ``axis``:

        - ``axis == RIGHT``  -> left-to-right
        - ``axis == LEFT``   -> right-to-left
        - ``axis == UP``     -> bottom-to-top
        - ``axis == DOWN``   -> top-to-bottom

        Each piece keeps the original's perpendicular extent and gets
        ``1/k`` of the size along ``axis``. The union of the pieces equals
        ``self``; their centers split the axis dimension at uniform offsets.
        """
        if k < 1:
            raise ValueError(f"k must be >= 1, got {k}")
        direction = _as_dir(axis)
        horizontal = direction[0] != 0
        vertical = direction[1] != 0
        if horizontal == vertical:
            raise ValueError(
                "axis must be a single cardinal direction (RIGHT/LEFT/UP/DOWN), "
                f"got {direction.tolist()}"
            )
        cls = type(self)
        pieces: list[Region] = []
        if horizontal:
            step = self.width / k
            for i in range(k):
                left = self.left + i * step
                pieces.append(cls(top=self.top, bottom=self.bottom, left=left, right=left + step))
            if direction[0] < 0:
                pieces.reverse()
        else:
            step = self.height / k
            for i in range(k):
                bottom = self.bottom + i * step
                pieces.append(
                    cls(top=bottom + step, bottom=bottom, left=self.left, right=self.right)
                )
            if direction[1] < 0:
                pieces.reverse()
        return pieces

    def linspace(
        self,
        axis: np.ndarray | Iterable[float],
        k: int,
        *,
        inset: float = 0.0,
        include_edges: bool = False,
        orthogonal: float | None = None,
    ) -> list[np.ndarray]:
        """Return ``k`` evenly spaced points along ``axis`` inside this region.

        Default behavior leaves equal margins so the distance from each edge to
        the nearest point equals the distance between points. Points are centered
        on the perpendicular axis unless ``orthogonal`` is provided. Ordering
        follows ``axis`` (RIGHT -> left-to-right, LEFT -> right-to-left,
        UP -> bottom-to-top, DOWN -> top-to-bottom).

        Args:
            axis: Cardinal Manim direction (RIGHT/LEFT/UP/DOWN).
            k: Number of points to return.
            inset: Extra margin to carve out on both ends before spacing.
            include_edges: If true, the first/last points sit on the inset edges.
            orthogonal: Optional fixed coordinate along the perpendicular axis.
        """
        if k < 1:
            raise ValueError(f"k must be >= 1, got {k}")
        if inset < 0:
            raise ValueError(f"inset must be >= 0, got {inset}")
        direction = _as_dir(axis)
        horizontal = direction[0] != 0
        vertical = direction[1] != 0
        if horizontal == vertical:
            raise ValueError(
                "axis must be a single cardinal direction (RIGHT/LEFT/UP/DOWN), "
                f"got {direction.tolist()}"
            )

        span = self.width if horizontal else self.height
        usable = span - 2 * inset
        if usable < 0:
            raise ValueError(
                f"inset is too large for the region extent; got inset={inset} for span={span}"
            )
        if usable == 0 and k > 1:
            raise ValueError("inset leaves no room for multiple points")

        if horizontal:
            start = self.left + inset
            end = self.right - inset
            other = self.center[1] if orthogonal is None else orthogonal
            if include_edges:
                if k == 1:
                    coords = [start]
                else:
                    step = (end - start) / (k - 1)
                    coords = [start + i * step for i in range(k)]
            else:
                step = (end - start) / (k + 1)
                coords = [start + (i + 1) * step for i in range(k)]
            points = [np.array([x, other, 0.0]) for x in coords]
        else:
            start = self.bottom + inset
            end = self.top - inset
            other = self.center[0] if orthogonal is None else orthogonal
            if include_edges:
                if k == 1:
                    coords = [start]
                else:
                    step = (end - start) / (k - 1)
                    coords = [start + i * step for i in range(k)]
            else:
                step = (end - start) / (k + 1)
                coords = [start + (i + 1) * step for i in range(k)]
            points = [np.array([other, y, 0.0]) for y in coords]

        if direction[0] < 0 or direction[1] < 0:
            points.reverse()
        return points
