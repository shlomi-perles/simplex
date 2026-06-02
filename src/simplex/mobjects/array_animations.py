"""Animation helpers for :mod:`simplex.mobjects.array`."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, cast

import numpy as np
from manim import (
    DOWN,
    TAU,
    Animation,
    AnimationGroup,
    ArcBetweenPoints,
    FadeOut,
    MoveAlongPath,
    Restore,
    Transform,
    Wait,
)

from simplex.mobjects.array import Array, ArrayCell, CellValue

_INSERT_ENTRANCE_SHIFT_FRACTION = 1 / 2


class _ArrayAnimationGroup(AnimationGroup):
    """AnimationGroup with a small cleanup hook for semantic state updates."""

    def __init__(  # pyright: ignore[reportInconsistentConstructor]
        self,
        *animations: Animation,
        cleanup: Callable[[], None] | None = None,
        **kwargs: Any,
    ) -> None:
        self._cleanup = cleanup
        super().__init__(*animations, **kwargs)

    def clean_up_from_scene(self, scene: Any) -> None:
        super().clean_up_from_scene(scene)
        if self._cleanup is not None:
            self._cleanup()
            self._cleanup = None


def animate_set_value(
    array: Array,
    index: int,
    value: CellValue,
    **kwargs: Any,
) -> AnimationGroup:
    """Animate replacing the value at ``index``."""
    cell = array.cell(index)
    target = cell.make_value_mobject(value)

    def cleanup() -> None:
        array.set_value(index, value)

    return _ArrayAnimationGroup(
        Transform(cast(Any, cell.value_mobject), cast(Any, target)),
        cleanup=cleanup,
        **kwargs,
    )


def animate_insert(
    array: Array,
    index: int,
    value: CellValue,
    *,
    slide_in: float | None = None,
    **kwargs: Any,
) -> AnimationGroup:
    """Animate inserting a new cell before visible ``index``."""
    offset = array._offset_for_index(index, allow_end=True)
    old_cells = array.iter_cells()
    old_centers = [cell.frame_center.copy() for cell in old_cells]
    old_label_center = _label_center(array)

    new_cell = array._insert_cell_at_offset(offset, value, relayout=False)
    array._refresh_indices()
    _relayout_after_insert(array, offset, old_cells, old_centers)

    target_centers = [cell.frame_center.copy() for cell in old_cells]
    new_target = new_cell.frame_center.copy()
    target_label_center = _label_center(array)

    for cell, center in zip(old_cells, old_centers, strict=True):
        cell.move_frame_to(center)
    _move_label_to(array, old_label_center)

    new_cell.save_state()
    shift_distance = slide_in
    if shift_distance is None:
        shift_distance = _cell_motion_extent(array, new_cell) * _INSERT_ENTRANCE_SHIFT_FRACTION
    entry_direction = -array.direction if offset == 0 else array.direction
    start = new_target + entry_direction * shift_distance
    new_cell.move_frame_to(start)
    new_cell.set_opacity(0.0)

    animations: list[Animation] = [Restore(new_cell)]
    animations.extend(_shift_cells(old_cells, old_centers, target_centers))
    if old_label_center is not None and target_label_center is not None:
        animations.extend(_shift_label(array, old_label_center, target_label_center))
    return _ArrayAnimationGroup(*animations, **kwargs)


def animate_remove(
    array: Array,
    index: int,
    *,
    shift: np.ndarray = DOWN,
    **kwargs: Any,
) -> AnimationGroup:
    """Animate removing the cell at visible ``index``."""
    offset = array._offset_for_index(index)
    old_cells = array.iter_cells()
    old_centers = [cell.frame_center.copy() for cell in old_cells]
    old_label_center = _label_center(array)
    removed = array._cell_at_offset(offset)
    survivor_cells = tuple(cell for cell in old_cells if cell is not removed)

    array._remove_cell_at_offset(offset, relayout=False)
    array.add(removed)
    _relayout_after_remove(array, offset, removed, old_cells, old_centers)

    survivor_targets = [cell.frame_center.copy() for cell in survivor_cells]
    target_label_center = _label_center(array)

    for cell, center in zip(old_cells, old_centers, strict=True):
        cell.move_frame_to(center)
    _move_label_to(array, old_label_center)

    animations: list[Animation] = [FadeOut(removed, shift=shift)]
    animations.extend(_shift_cells(survivor_cells, _centers_for(survivor_cells), survivor_targets))
    if old_label_center is not None and target_label_center is not None:
        animations.extend(_shift_label(array, old_label_center, target_label_center))

    def cleanup() -> None:
        array.remove(removed)

    return _ArrayAnimationGroup(*animations, cleanup=cleanup, **kwargs)


def animate_swap(
    array: Array,
    i: int,
    j: int,
    *,
    arc_angle: float = TAU / 4,
    **kwargs: Any,
) -> AnimationGroup:
    """Animate swapping two visible cells."""
    if i == j:
        return _ArrayAnimationGroup(Wait(run_time=0), **kwargs)

    offset_i = array._offset_for_index(i)
    offset_j = array._offset_for_index(j)
    cell_i = array._cell_at_offset(offset_i)
    cell_j = array._cell_at_offset(offset_j)
    anchor = array._cell_at_offset(0).frame_center.copy()
    start_i = cell_i.frame_center
    start_j = cell_j.frame_center
    path_i = ArcBetweenPoints(start_i, start_j, angle=arc_angle)
    path_j = ArcBetweenPoints(start_j, start_i, angle=arc_angle)

    def cleanup() -> None:
        array.cells.submobjects[offset_i], array.cells.submobjects[offset_j] = (
            array.cells.submobjects[offset_j],
            array.cells.submobjects[offset_i],
        )
        array.relayout(anchor_point=anchor)

    return _ArrayAnimationGroup(
        MoveAlongPath(cast(Any, cell_i), path_i),
        MoveAlongPath(cast(Any, cell_j), path_j),
        cleanup=cleanup,
        **kwargs,
    )


def _relayout_after_insert(
    array: Array,
    offset: int,
    old_cells: tuple[ArrayCell, ...],
    old_centers: list[np.ndarray],
) -> None:
    if not old_cells:
        array.relayout()
        return
    anchor_offset = 1 if offset == 0 else 0
    array.relayout(anchor_index=anchor_offset, anchor_point=old_centers[0])


def _relayout_after_remove(
    array: Array,
    offset: int,
    removed: ArrayCell,
    old_cells: tuple[ArrayCell, ...],
    old_centers: list[np.ndarray],
) -> None:
    if len(old_cells) <= 1:
        return
    anchor = removed.frame_center if offset == 0 else old_centers[0]
    array.relayout(anchor_index=0, anchor_point=anchor)


def _centers_for(cells: tuple[ArrayCell, ...]) -> list[np.ndarray]:
    return [cell.frame_center.copy() for cell in cells]


def _cell_motion_extent(array: Array, cell: ArrayCell) -> float:
    return cell.frame.width if abs(array.direction[0]) > 0 else cell.frame.height


def _shift_cells(
    cells: tuple[ArrayCell, ...],
    starts: list[np.ndarray],
    targets: list[np.ndarray],
) -> list[Animation]:
    animations: list[Animation] = []
    for cell, start, target in zip(cells, starts, targets, strict=True):
        delta = target - start
        if np.linalg.norm(delta) > 1e-9:
            animations.append(cast(Animation, cell.animate.shift(delta)))
    return animations


def _label_center(array: Array) -> np.ndarray | None:
    if array.label_mobject is None:
        return None
    return np.asarray(array.label_mobject.get_center(), dtype=float)


def _move_label_to(array: Array, center: np.ndarray | None) -> None:
    if array.label_mobject is not None and center is not None:
        array.label_mobject.move_to(center)


def _shift_label(
    array: Array,
    start: np.ndarray,
    target: np.ndarray,
) -> list[Animation]:
    if array.label_mobject is None:
        return []
    delta = target - start
    if np.linalg.norm(delta) <= 1e-9:
        return []
    return [cast(Animation, array.label_mobject.animate.shift(delta))]


__all__ = ["animate_insert", "animate_remove", "animate_set_value", "animate_swap"]
