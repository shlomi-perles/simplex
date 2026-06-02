"""One-dimensional array mobjects for algorithm visualizations.

``Array`` models fixed array slots: frames and indices belong to positions,
while values are the content that changes or moves between positions. Structural
helpers such as insert/remove shift slots; swap helpers animate the values.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any, cast

import numpy as np
from manim import (
    DOWN,
    DR,
    LEFT,
    ORIGIN,
    RIGHT,
    SMALL_BUFF,
    UP,
    Animation,
    AnimationGroup,
    Arrow,
    Indicate,
    MathTex,
    Mobject,
    Square,
    Tex,
    Transform,
    VGroup,
    VMobject,
)
from manim.mobject.opengl.opengl_compatibility import ConvertToOpenGL

from simplex.engine.opengl_compat import MobjectLike, is_mobject
from simplex.engine.region import Region
from simplex.engine.scaling import scale_to_fit
from simplex.theme.context import get_active_theme

type CellValue = str | int | float | MobjectLike | None
type LabelFactory = Callable[[CellValue], MobjectLike]

_PHANTOM_VALUE = r"\phantom{0}"
_CARDINAL_DIRECTIONS = (UP, DOWN, LEFT, RIGHT)
_VALUE_SIZE_FRACTION = 4 / 5
_LABEL_SIZE_FRACTION = 4 / 5
_LABEL_BUFF_FRACTION = 1 / 5
_INDEX_SIZE_FRACTION = 1 / 4
_INDEX_INSET_FRACTION = 1 / 20
_POINTER_LENGTH_FRACTION = 1 / 2
_POINTER_LABEL_SCALE = 1 / 2


def _is_blank(value: CellValue) -> bool:
    return not is_mobject(value) and (value is None or value == "")


def _copy_if_mobject(value: CellValue) -> MobjectLike | None:
    if not is_mobject(value):
        return None
    return cast(MobjectLike, cast(Any, value).copy())


def _as_point(point: np.ndarray | Iterable[float]) -> np.ndarray:
    arr = np.asarray(point, dtype=float)
    if arr.shape == (2,):
        arr = np.append(arr, 0.0)
    if arr.shape != (3,):
        raise ValueError(f"point must be a 2D or 3D vector, got shape {arr.shape}")
    return arr


def _as_cardinal(direction: np.ndarray | Iterable[float]) -> np.ndarray:
    arr = _as_point(direction)
    signs = np.sign(arr).astype(float)
    if not any(np.allclose(signs, candidate) for candidate in _CARDINAL_DIRECTIONS):
        raise ValueError(
            "direction must be one of Manim's cardinal vectors: UP, DOWN, LEFT, or RIGHT"
        )
    return signs


def _as_anchor(anchor: np.ndarray | Iterable[float]) -> np.ndarray:
    arr = _as_point(anchor)
    signs = np.sign(arr).astype(float)
    if np.allclose(signs, ORIGIN):
        raise ValueError("anchor must point to an edge or corner, not ORIGIN")
    return signs


def _is_horizontal(direction: np.ndarray) -> bool:
    return bool(abs(direction[0]) > 0)


def _coerce_values(values: Iterable[CellValue] | CellValue | None) -> list[CellValue]:
    if values is None:
        return []
    if isinstance(values, str | int | float) or is_mobject(values):
        return [values]
    return list(values)


def _default_label(value: CellValue, *, config: dict[str, Any]) -> MobjectLike:
    copied = _copy_if_mobject(value)
    if copied is not None:
        return copied
    return MathTex(_PHANTOM_VALUE if _is_blank(value) else str(value), **config)


class ArrayCell(VGroup, metaclass=ConvertToOpenGL):
    """A single array slot: frame, centered value, and optional index label."""

    def __init__(
        self,
        value: CellValue = None,
        *,
        index: CellValue = None,
        frame_scale: float = 1.0,
        value_scale: float = _VALUE_SIZE_FRACTION,
        index_scale: float = _INDEX_SIZE_FRACTION,
        index_anchor: np.ndarray | Iterable[float] = DR,
        index_buff: float | None = None,
        frame_type: type[VMobject] = Square,
        frame_config: dict[str, Any] | None = None,
        value_config: dict[str, Any] | None = None,
        index_config: dict[str, Any] | None = None,
        value_factory: LabelFactory | None = None,
        index_factory: LabelFactory | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)

        self.value: CellValue = value
        self.index: CellValue = index
        self.frame_scale = frame_scale
        self.value_scale = value_scale
        self.index_scale = index_scale
        self.index_anchor = _as_anchor(index_anchor)
        self.index_buff = index_buff
        self.value_config = dict(value_config or {})
        self.index_config = dict(index_config or {})
        self.value_factory = value_factory
        self.index_factory = index_factory

        frame_opts = dict(frame_config or {})
        self.frame: VMobject = frame_type(**frame_opts)
        if frame_scale != 1:
            self.frame.scale(frame_scale)

        self.value_mobject = self.make_value_mobject(value)
        self.index_mobject: MobjectLike | None = None
        if not _is_blank(index):
            self.index_mobject = self.make_index_mobject(index)
        self._sync_submobjects()
        self._place_value()
        self._place_index()

    @property
    def frame_center(self) -> np.ndarray:
        """Return the center of the slot frame, ignoring external labels."""
        return np.asarray(self.frame.get_center(), dtype=float)

    def move_frame_to(self, point: np.ndarray | Iterable[float]) -> ArrayCell:
        """Move the whole cell so the frame center lands on ``point``."""
        self.shift(_as_point(point) - self.frame_center)
        return self

    def make_value_mobject(self, value: CellValue) -> MobjectLike:
        """Build and fit a value label for this cell without installing it."""
        mob = (
            self.value_factory(value)
            if self.value_factory is not None
            else _default_label(value, config=self.value_config)
        )
        if _is_blank(value):
            mob.set_opacity(0.0)
        self._fit_value_mobject(mob)
        return mob

    def make_index_mobject(self, index: CellValue) -> MobjectLike:
        """Build and fit an index label for this cell without installing it."""
        mob = (
            self.index_factory(index)
            if self.index_factory is not None
            else _default_label(index, config=self.index_config)
        )
        self._fit_index_mobject(mob)
        return mob

    def set_value(self, value: CellValue) -> ArrayCell:
        """Synchronously replace the value label."""
        self.value = value
        self.value_mobject = self.make_value_mobject(value)
        self._sync_submobjects()
        self._place_value()
        self._place_index()
        return self

    def set_index(self, index: CellValue) -> ArrayCell:
        """Synchronously replace, add, or remove the index label."""
        if index == self.index:
            self._place_index()
            return self
        self.index = index
        self.index_mobject = None if _is_blank(index) else self.make_index_mobject(index)
        self._sync_submobjects()
        self._place_value()
        self._place_index()
        return self

    def highlight(self, color: str | None = None, **kwargs: Any) -> Animation:
        """Return an attention animation for this cell."""
        color = color or get_active_theme().palette.accent
        return Indicate(self, color=color, **kwargs)

    def _sync_submobjects(self) -> None:
        self.remove(*tuple(self.submobjects))
        self.add(self.frame, cast(Any, self.value_mobject))
        if self.index_mobject is not None:
            self.add(cast(Any, self.index_mobject))

    def _content_region(self) -> Region:
        return Region(
            top=self.frame.get_top(),
            bottom=self.frame.get_bottom(),
            left=self.frame.get_left(),
            right=self.frame.get_right(),
        )

    def _fit_value_mobject(self, mob: MobjectLike) -> None:
        region = self._content_region()
        scale_to_fit(
            cast(Mobject, mob),
            len_x=region.width * self.value_scale,
            len_y=region.height * self.value_scale,
        )
        region.place(cast(Mobject, mob), ORIGIN)

    def _fit_index_mobject(self, mob: MobjectLike) -> None:
        scale_to_fit(
            cast(Mobject, mob),
            len_x=self.frame.width * self.index_scale,
            len_y=self.frame.height * self.index_scale,
        )

    def _place_value(self) -> None:
        self._fit_value_mobject(self.value_mobject)

    def _place_index(self) -> None:
        if self.index_mobject is None:
            return
        self._fit_index_mobject(self.index_mobject)
        frame_region = self._content_region()
        buff = self.index_buff
        if buff is None:
            buff = min(self.frame.width, self.frame.height) * _INDEX_INSET_FRACTION
        frame_region.place(cast(Mobject, self.index_mobject), self.index_anchor, buff=buff)


class Array(VGroup, metaclass=ConvertToOpenGL):
    """A theme-aware, one-dimensional array visualization.

    ``index`` arguments use the visible array indices, i.e. ``start_index`` is
    subtracted internally before indexing ``cells``.
    """

    def __init__(
        self,
        values: Iterable[CellValue] | CellValue | None = None,
        *,
        label: CellValue = None,
        show_indices: bool = False,
        start_index: int = 0,
        direction: np.ndarray | Iterable[float] = RIGHT,
        cell_buff: float = 0.0,
        label_buff: float | None = None,
        label_scale: float = _LABEL_SIZE_FRACTION,
        cell_config: dict[str, Any] | None = None,
        label_config: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.start_index = start_index
        self.show_indices = show_indices
        self.direction = _as_cardinal(direction)
        self.cell_buff = cell_buff
        self.label_buff = label_buff
        self.label_scale = label_scale
        self.cell_config = dict(cell_config or {})
        self.label_config = dict(label_config or {})

        self.label_mobject = self._make_label(label)
        self.cells = VGroup()
        if self.label_mobject is not None:
            self.add(cast(Any, self.label_mobject))
        self.add(self.cells)

        for value in _coerce_values(values):
            self.cells.add(self._make_cell(value, len(self.cells)))
        self.relayout(anchor_point=ORIGIN)
        self.center()

    @property
    def values(self) -> tuple[CellValue, ...]:
        """Current values in visible index order."""
        return tuple(cell.value for cell in self.iter_cells())

    def iter_cells(self) -> tuple[ArrayCell, ...]:
        """Return cells in visible index order."""
        return tuple(cast(ArrayCell, cell) for cell in self.cells)

    def cell(self, index: int) -> ArrayCell:
        """Return the cell at visible ``index``."""
        return self._cell_at_offset(self._offset_for_index(index))

    def get_entry(self, index: int) -> ArrayCell:
        """Compatibility alias for :meth:`cell`."""
        return self.cell(index)

    def set_value(self, index: int, value: CellValue) -> Array:
        """Synchronously replace the value at visible ``index``."""
        self.cell(index).set_value(value)
        return self

    def at(self, index: int, value: CellValue) -> Array:
        """Compatibility alias for :meth:`set_value`."""
        return self.set_value(index, value)

    def append(self, value: CellValue) -> Array:
        """Synchronously append a new cell."""
        self._insert_cell_at_offset(len(self.cells), value)
        return self

    def prepend(self, value: CellValue) -> Array:
        """Synchronously prepend a new cell."""
        self._insert_cell_at_offset(0, value)
        return self

    def insert_at(self, index: int, value: CellValue) -> Array:
        """Synchronously insert before visible ``index``.

        Passing ``start_index + len(cells)`` appends.
        """
        self._insert_cell_at_offset(self._offset_for_index(index, allow_end=True), value)
        return self

    def remove_at(self, index: int) -> Array:
        """Synchronously remove the cell at visible ``index``."""
        self._remove_cell_at_offset(self._offset_for_index(index))
        return self

    def swap(self, i: int, j: int) -> Array:
        """Synchronously swap two visible cells."""
        if i == j:
            return self
        a = self._offset_for_index(i)
        b = self._offset_for_index(j)
        anchor = self._cell_at_offset(0).frame_center.copy()
        self.cells.submobjects[a], self.cells.submobjects[b] = (
            self.cells.submobjects[b],
            self.cells.submobjects[a],
        )
        self.relayout(anchor_point=anchor)
        return self

    def relayout(
        self,
        *,
        anchor_index: int = 0,
        anchor_point: np.ndarray | Iterable[float] | None = None,
    ) -> Array:
        """Recompute cell positions while pinning one frame center."""
        if len(self.cells) == 0:
            if self.label_mobject is not None and anchor_point is not None:
                cast(Mobject, self.label_mobject).move_to(_as_point(anchor_point))
            return self

        anchor_index = int(np.clip(anchor_index, 0, len(self.cells) - 1))
        anchor = (
            self._cell_at_offset(anchor_index).frame_center
            if anchor_point is None
            else _as_point(anchor_point)
        )
        step = self._step_vector()
        origin = anchor - step * anchor_index
        for offset, cell in enumerate(self.iter_cells()):
            cell.move_frame_to(origin + step * offset)
        self._place_label()
        return self

    def indicate(self, index: int, color: str | None = None, **kwargs: Any) -> Animation:
        """Return an attention animation for one cell."""
        return self.cell(index).highlight(color=color, **kwargs)

    def indicate_at(self, index: int, color: str | None = None, **kwargs: Any) -> Animation:
        """Compatibility alias for :meth:`indicate`."""
        return self.indicate(index, color=color, **kwargs)

    def animate_set_value(self, index: int, value: CellValue, **kwargs: Any) -> AnimationGroup:
        """Animate replacing one value."""
        from simplex.mobjects.array_animations import animate_set_value

        return animate_set_value(self, index, value, **kwargs)

    def animate_append(self, value: CellValue, **kwargs: Any) -> AnimationGroup:
        """Animate appending a cell."""
        from simplex.mobjects.array_animations import animate_insert

        index = self.start_index + len(self.cells)
        return animate_insert(self, index, value, **kwargs)

    def animate_prepend(self, value: CellValue, **kwargs: Any) -> AnimationGroup:
        """Animate prepending a cell."""
        from simplex.mobjects.array_animations import animate_insert

        return animate_insert(self, self.start_index, value, **kwargs)

    def animate_insert_at(self, index: int, value: CellValue, **kwargs: Any) -> AnimationGroup:
        """Animate inserting a cell before visible ``index``."""
        from simplex.mobjects.array_animations import animate_insert

        return animate_insert(self, index, value, **kwargs)

    def animate_remove(self, index: int | None = None, **kwargs: Any) -> AnimationGroup:
        """Animate removing one cell. Defaults to the last cell."""
        from simplex.mobjects.array_animations import animate_remove

        if index is None:
            index = self.start_index + len(self.cells) - 1
        return animate_remove(self, index, **kwargs)

    def animate_swap(self, i: int, j: int, **kwargs: Any) -> AnimationGroup:
        """Animate swapping values between two visible indices."""
        from simplex.mobjects.array_animations import animate_swap

        return animate_swap(self, i, j, **kwargs)

    def push(
        self,
        value: CellValue,
        *,
        side: np.ndarray | Iterable[float] = RIGHT,
        **kwargs: Any,
    ) -> AnimationGroup:
        """Compatibility alias for animated append/prepend."""
        side = _as_cardinal(side)
        if np.allclose(side, LEFT):
            return self.animate_prepend(value, **kwargs)
        return self.animate_append(value, **kwargs)

    def pop(self, index: int | None = None, **kwargs: Any) -> AnimationGroup:
        """Compatibility alias for :meth:`animate_remove`."""
        return self.animate_remove(index, **kwargs)

    def _make_label(self, label: CellValue) -> MobjectLike | None:
        if _is_blank(label):
            return None
        copied = _copy_if_mobject(label)
        if copied is not None:
            return copied
        return Tex(str(label), **self.label_config)

    def _make_cell(self, value: CellValue, offset: int) -> ArrayCell:
        index = self.start_index + offset if self.show_indices else None
        return ArrayCell(value, index=index, **self.cell_config)

    def _cell_at_offset(self, offset: int) -> ArrayCell:
        return cast(ArrayCell, self.cells[offset])

    def _offset_for_index(self, index: int, *, allow_end: bool = False) -> int:
        offset = index - self.start_index
        upper = len(self.cells) if allow_end else len(self.cells) - 1
        if offset < 0 or offset > upper:
            end = self.start_index + len(self.cells) - (0 if allow_end else 1)
            raise IndexError(f"array index {index} out of range [{self.start_index}, {end}]")
        return offset

    def _insert_cell_at_offset(
        self,
        offset: int,
        value: CellValue,
        *,
        relayout: bool = True,
    ) -> ArrayCell:
        old_first = self._cell_at_offset(0) if len(self.cells) else None
        old_first_center = None if old_first is None else old_first.frame_center.copy()
        cell = self._make_cell(value, offset)
        self._match_existing_cell_geometry(cell)
        self.cells.insert(offset, cell)
        self._refresh_indices()
        if relayout:
            if old_first_center is None:
                self.relayout(anchor_point=ORIGIN)
            else:
                anchor_offset = 1 if offset == 0 else 0
                self.relayout(anchor_index=anchor_offset, anchor_point=old_first_center)
        return cell

    def _remove_cell_at_offset(self, offset: int, *, relayout: bool = True) -> ArrayCell:
        removed = self._cell_at_offset(offset)
        anchor_point: np.ndarray | None = None
        anchor_index = 0
        if len(self.cells) > 1:
            if offset == 0:
                anchor_point = removed.frame_center.copy()
            else:
                anchor_point = self._cell_at_offset(0).frame_center.copy()
        self.cells.remove(removed)
        self._refresh_indices()
        if relayout and anchor_point is not None:
            self.relayout(anchor_index=anchor_index, anchor_point=anchor_point)
        return removed

    def _refresh_indices(self) -> None:
        for offset, cell in enumerate(self.iter_cells()):
            cell.set_index(self.start_index + offset if self.show_indices else None)

    def _place_label(self) -> None:
        if self.label_mobject is None or len(self.cells) == 0:
            return
        frames = self._frames()
        self._fit_label_mobject()
        cast(Mobject, self.label_mobject).next_to(
            frames,
            -self.direction,
            buff=self._label_buff(),
        )

    def _step_vector(self) -> np.ndarray:
        if len(self.cells) == 0:
            return self.direction
        reference = self._cell_at_offset(0).frame
        extent = reference.width if _is_horizontal(self.direction) else reference.height
        return self.direction * (extent + self.cell_buff)

    def _frames(self) -> VGroup:
        return VGroup(*(cell.frame for cell in self.iter_cells()))

    def _cell_extent(self) -> float:
        reference = self._cell_at_offset(0).frame
        return reference.height if _is_horizontal(self.direction) else reference.width

    def _fit_label_mobject(self) -> None:
        if self.label_mobject is None:
            return
        if _is_horizontal(self.direction):
            scale_to_fit(
                cast(Mobject, self.label_mobject),
                len_y=self._cell_extent() * self.label_scale,
            )
        else:
            scale_to_fit(
                cast(Mobject, self.label_mobject),
                len_x=self._cell_extent() * self.label_scale,
            )

    def _label_buff(self) -> float:
        if self.label_buff is not None:
            return self.label_buff
        return self._cell_extent() * _LABEL_BUFF_FRACTION

    def _match_existing_cell_geometry(self, cell: ArrayCell) -> None:
        if len(self.cells) == 0:
            return
        reference = self._cell_at_offset(0).frame
        if cell.frame.width <= 0:
            return
        cell.frame.scale(reference.width / cell.frame.width)
        cell._place_value()
        cell._place_index()


class ArrayPointer(VGroup, metaclass=ConvertToOpenGL):
    """An arrow pointing at one ``Array`` cell, with an optional label."""

    def __init__(
        self,
        array: Array,
        index: int,
        label: CellValue = None,
        *,
        direction: np.ndarray | Iterable[float] = DOWN,
        length: float | None = None,
        buff: float = SMALL_BUFF,
        label_buff: float = SMALL_BUFF,
        label_scale: float = _POINTER_LABEL_SCALE,
        label_config: dict[str, Any] | None = None,
        color: str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        theme = get_active_theme()
        self.array = array
        self.index = index
        self.direction = _as_cardinal(direction)
        self.buff = buff
        self.label_buff = label_buff
        self.label_scale = label_scale
        self.label_config = dict(label_config or {})
        self.pointer_color = color or theme.palette.accent
        if length is None:
            frame = self.array.cell(self.index).frame
            length = min(frame.width, frame.height) * _POINTER_LENGTH_FRACTION

        self.arrow = Arrow(
            start=ORIGIN,
            end=self.direction * length,
            buff=0.0,
            color=self.pointer_color,
        )
        self.label_mobject = self._make_label(label)
        self.add(self.arrow)
        if self.label_mobject is not None:
            self.add(cast(Any, self.label_mobject))
        self._place()

    def set_index(self, index: int, label: CellValue | None = None) -> ArrayPointer:
        """Synchronously point at another cell."""
        self.index = index
        if label is not None:
            self.set_label(label)
        self._place()
        return self

    def set_label(self, label: CellValue) -> ArrayPointer:
        """Synchronously replace the pointer label."""
        if self.label_mobject is not None:
            self.remove(cast(Mobject, self.label_mobject))
        self.label_mobject = self._make_label(label)
        if self.label_mobject is not None:
            self.add(cast(Any, self.label_mobject))
        self._place_label()
        return self

    def animate_to(
        self,
        index: int,
        *,
        label: CellValue | None = None,
        **kwargs: Any,
    ) -> Animation:
        """Animate this pointer to another cell."""
        target = self.copy()
        target.array = self.array
        target.index = index
        if label is not None:
            target.set_label(label)
        target._place()
        self.index = index
        return Transform(self, target, **kwargs)

    def to_entry(
        self,
        index: int,
        *,
        text: CellValue | None = None,
        label: CellValue | None = None,
        **kwargs: Any,
    ) -> Animation:
        """Compatibility alias for :meth:`animate_to`."""
        return self.animate_to(index, label=label if label is not None else text, **kwargs)

    def _make_label(self, label: CellValue) -> MobjectLike | None:
        if _is_blank(label):
            return None
        copied = _copy_if_mobject(label)
        if copied is not None:
            copied.scale(self.label_scale)
            copied.set_color(self.pointer_color)
            return copied
        opts = dict(self.label_config)
        opts.setdefault("color", self.pointer_color)
        mob = MathTex(str(label), **opts)
        mob.scale(self.label_scale)
        return mob

    def _place(self) -> None:
        self.arrow.next_to(
            self.array.cell(self.index).frame,
            -self.direction,
            buff=self.buff,
        )
        self._place_label()

    def _place_label(self) -> None:
        if self.label_mobject is None:
            return
        cast(Mobject, self.label_mobject).next_to(
            self.arrow,
            -self.direction,
            buff=self.label_buff,
        )


ArrayEntry = ArrayCell
ArrayMob = Array

__all__ = [
    "Array",
    "ArrayCell",
    "ArrayEntry",
    "ArrayMob",
    "ArrayPointer",
    "CellValue",
]
