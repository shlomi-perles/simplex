"""Region -- mutable rectangular sub-area of the frame.

The region API speaks in Manim's direction vectors (``UP``, ``DR``, ``ORIGIN``,
...) rather than ad-hoc strings. ``Region`` subclasses Manim's transparent
``Rectangle`` so placement can use the same geometry primitives as ordinary
mobjects.
"""

from collections.abc import Callable, Iterable
from numbers import Real
from typing import Any, Self, cast

import numpy as np
from manim import DEFAULT_MOBJECT_TO_EDGE_BUFFER, MED_LARGE_BUFF, Rectangle
from manim.mobject.opengl.opengl_compatibility import ConvertToOpenGL

from simplex.engine.opengl_compat import MobjectLike, critical_point, is_mobject

type EdgeValue = float | np.ndarray | Iterable[float] | MobjectLike

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
    if is_mobject(value):
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


class Region(Rectangle, metaclass=ConvertToOpenGL):
    """A transparent, mutable, axis-aligned region in Manim frame coordinates."""

    def __init__(
        self,
        *,
        top: EdgeValue,
        bottom: EdgeValue,
        left: EdgeValue,
        right: EdgeValue,
        **kwargs: Any,
    ) -> None:
        top_f = _edge_value("top", top)
        bottom_f = _edge_value("bottom", bottom)
        left_f = _edge_value("left", left)
        right_f = _edge_value("right", right)
        width = right_f - left_f
        height = top_f - bottom_f
        if width < 0 or height < 0:
            raise ValueError(
                "region edges must satisfy left <= right and bottom <= top; "
                f"got top={top_f}, bottom={bottom_f}, left={left_f}, right={right_f}"
            )

        kwargs.setdefault("stroke_width", 0)
        kwargs.setdefault("stroke_opacity", 0)
        kwargs.setdefault("fill_opacity", 0)
        super().__init__(width=width, height=height, **kwargs)
        self.move_to(np.array([(left_f + right_f) / 2, (top_f + bottom_f) / 2, 0.0]))

    @classmethod
    def full_frame(cls) -> Self:
        from manim import config

        half_w = config.frame_width / 2
        half_h = config.frame_height / 2
        return cls(top=half_h, bottom=-half_h, left=-half_w, right=half_w)

    @property
    def top(self) -> float:
        return float(self.get_top()[1])

    @top.setter
    def top(self, value: EdgeValue) -> None:
        self._apply_edges(top=_edge_value("top", value))

    @property
    def bottom(self) -> float:
        return float(self.get_bottom()[1])

    @bottom.setter
    def bottom(self, value: EdgeValue) -> None:
        self._apply_edges(bottom=_edge_value("bottom", value))

    @property
    def left(self) -> float:
        return float(self.get_left()[0])

    @left.setter
    def left(self, value: EdgeValue) -> None:
        self._apply_edges(left=_edge_value("left", value))

    @property
    def right(self) -> float:
        return float(self.get_right()[0])

    @right.setter
    def right(self, value: EdgeValue) -> None:
        self._apply_edges(right=_edge_value("right", value))

    def _apply_edges(
        self,
        *,
        top: float | None = None,
        bottom: float | None = None,
        left: float | None = None,
        right: float | None = None,
    ) -> None:
        top_f = self.top if top is None else top
        bottom_f = self.bottom if bottom is None else bottom
        left_f = self.left if left is None else left
        right_f = self.right if right is None else right
        width = right_f - left_f
        height = top_f - bottom_f
        if width < 0 or height < 0:
            raise ValueError(
                "region edges must satisfy left <= right and bottom <= top; "
                f"got top={top_f}, bottom={bottom_f}, left={left_f}, right={right_f}"
            )
        self.stretch_to_fit_width(width)
        self.stretch_to_fit_height(height)
        self.move_to(np.array([(left_f + right_f) / 2, (top_f + bottom_f) / 2, 0.0]))

    def _anchor_point(self, direction: np.ndarray) -> np.ndarray:
        """Map a normalized direction vector to the matching point of this region."""
        return critical_point(self, direction)

    @property
    def always(self) -> "_RegionUpdaterBuilder":
        """Call region helpers every frame.

        ``place`` is special: the updater belongs to the placed mobject so it
        can keep following an animated region while Manim suspends the region's
        own updaters during ``region.animate``.
        """
        return _RegionUpdaterBuilder(self)

    def place(
        self,
        mob: MobjectLike,
        anchor: np.ndarray | Iterable[float] | None = None,
        buff: float = DEFAULT_MOBJECT_TO_EDGE_BUFFER,
    ) -> MobjectLike:
        """Move ``mob`` so its anchor sits at the matching point of this region.

        ``anchor`` is a Manim direction vector (``UP``, ``DR``, ``ORIGIN``, ...).
        ``buff`` pulls ``mob`` inward by that distance along the anchored axes.
        """
        from manim import ORIGIN

        direction = _as_dir(ORIGIN if anchor is None else anchor)
        mob.move_to(critical_point(self, direction), aligned_edge=direction)
        if buff:
            mob.shift(-direction * buff)
        return mob

    def scale_and_place(
        self,
        mob: MobjectLike,
        anchor: np.ndarray | Iterable[float] | None = None,
        *,
        buff: float = MED_LARGE_BUFF,
        scale_kwargs: dict[str, Any] | None = None,
        place_kwargs: dict[str, Any] | None = None,
    ) -> MobjectLike:
        """Scale ``mob`` to fit this region, then place it with ``place``.

        ``buff`` is the scaling buffer. Use ``scale_kwargs`` for additional
        ``scale_to_fit_mobject`` options and ``place_kwargs`` for ``place``
        options such as an edge-placement buffer.
        """
        from simplex.engine.scaling import scale_to_fit_mobject

        scale_options = dict(scale_kwargs or {})
        scale_options.setdefault("buff", buff)
        scale_to_fit_mobject(cast(Any, mob), self, **scale_options)
        return self.place(mob, anchor, **dict(place_kwargs or {}))

    def update(
        self,
        dt: float = 0,
        recursive: bool = True,
        *,
        top: EdgeValue | None = None,
        bottom: EdgeValue | None = None,
        left: EdgeValue | None = None,
        right: EdgeValue | None = None,
    ) -> Self:
        """Update region edges from floats, points, or neighbouring mobjects.

        Point values contribute their relevant coordinate: x for left/right,
        y for top/bottom. Mobjects contribute the edge facing this region, then
        use the same coordinate rule. With no edge arguments, this delegates to
        Manim's normal updater machinery.
        """
        if top is None and bottom is None and left is None and right is None:
            super().update(dt=dt, recursive=recursive)
            return self

        self._apply_edges(
            top=None if top is None else _edge_value("top", top),
            bottom=None if bottom is None else _edge_value("bottom", bottom),
            left=None if left is None else _edge_value("left", left),
            right=None if right is None else _edge_value("right", right),
        )
        return self

    def shrink(
        self,
        *,
        top: float = 0.0,
        bottom: float = 0.0,
        left: float = 0.0,
        right: float = 0.0,
    ) -> None:
        self._apply_edges(
            top=self.top - top,
            bottom=self.bottom + bottom,
            left=self.left + left,
            right=self.right - right,
        )

    def reset(self) -> None:
        full = Region.full_frame()
        self._apply_edges(top=full.top, bottom=full.bottom, left=full.left, right=full.right)

    def split_regions(
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
            other = self.get_center()[1] if orthogonal is None else orthogonal
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
            other = self.get_center()[0] if orthogonal is None else orthogonal
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


class _RegionUpdaterBuilder:
    """Region-specific ``always`` sugar."""

    def __init__(self, region: Region) -> None:
        self._region = region

    def place(
        self,
        mob: MobjectLike,
        anchor: np.ndarray | Iterable[float] | None = None,
        buff: float = DEFAULT_MOBJECT_TO_EDGE_BUFFER,
    ) -> Self:
        def updater(placed_mob: MobjectLike) -> None:
            self._region.place(placed_mob, anchor, buff=buff)

        cast(Any, mob).add_updater(updater, call_updater=True)
        return self

    def __getattr__(self, name: str) -> Callable[..., "_RegionUpdaterBuilder"]:
        def add_updater(*method_args: Any, **method_kwargs: Any) -> _RegionUpdaterBuilder:
            self._region.add_updater(
                lambda region: getattr(region, name)(*method_args, **method_kwargs),
                call_updater=True,
            )
            return self

        return add_updater
