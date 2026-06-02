"""Array mobject construction and state semantics."""

from typing import Any, cast

import numpy as np
import pytest

pytest.importorskip("manim")

from manim import Circle, VGroup

import simplex
from simplex.mobjects import Array, ArrayCell, ArrayEntry, ArrayMob, ArrayPointer


class _SceneStub:
    def add(self, *mobjects: object) -> None:
        pass

    def remove(self, *mobjects: object) -> None:
        pass


def test_array_exports_new_names_and_aliases() -> None:
    assert simplex.Array is Array
    assert simplex.ArrayCell is ArrayCell
    assert ArrayMob is Array
    assert ArrayEntry is ArrayCell


def test_array_constructs_with_indices_and_label() -> None:
    array = Array(["a", "b", "c"], label="A:", show_indices=True, start_index=1)

    assert len(array.cells) == 3
    assert array.values == ("a", "b", "c")
    assert array.cell(1).value == "a"
    assert array.cell(3).index == 3
    assert array.label_mobject is not None


def test_default_index_is_inside_dr_corner() -> None:
    array = Array(["a"], show_indices=True)
    cell = array.cell(0)
    index = cell.index_mobject
    assert index is not None

    assert index.get_right()[0] <= cell.frame.get_right()[0]
    assert index.get_bottom()[1] >= cell.frame.get_bottom()[1]
    assert index.get_center()[0] > cell.frame_center[0]
    assert index.get_center()[1] < cell.frame_center[1]


def test_array_label_uses_frame_geometry_not_indices() -> None:
    array = Array(["a", "b"], label="A:", show_indices=True)
    frames = VGroup(*(cell.frame for cell in array.iter_cells()))
    label = array.label_mobject
    assert label is not None

    cell_height = array.cell(0).frame.height
    assert label.get_center()[1] == pytest.approx(frames.get_center()[1])
    assert label.height == pytest.approx(cell_height * 4 / 5)
    assert frames.get_left()[0] - label.get_right()[0] == pytest.approx(cell_height / 5)


def test_cell_frame_type_uses_manim_shape_defaults() -> None:
    cell = ArrayCell("x", index=0, frame_type=Circle)

    assert isinstance(cell.frame, Circle)
    assert cell.frame.width == pytest.approx(Circle().width)


def test_array_rejects_out_of_range_visible_index() -> None:
    array = Array([1, 2], start_index=5)

    with pytest.raises(IndexError):
        array.cell(4)
    with pytest.raises(IndexError):
        array.cell(7)


def test_set_value_keeps_cell_frame_center_stable() -> None:
    array = Array(["1", "2"], show_indices=True)
    before = array.cell(0).frame_center.copy()

    array.set_value(0, "long")

    assert array.values == ("long", "2")
    assert np.allclose(array.cell(0).frame_center, before)


def test_insert_remove_and_append_keep_indices_contiguous() -> None:
    array = Array(["a", "c"], show_indices=True, start_index=1)

    array.insert_at(2, "b").append("d").remove_at(3)

    assert array.values == ("a", "b", "d")
    assert [cell.index for cell in array.iter_cells()] == [1, 2, 3]


def test_swap_exchanges_whole_cells() -> None:
    array = Array(["a", "b", "c"], show_indices=True, start_index=1)
    first, second, third = array.iter_cells()
    first_center = first.frame_center.copy()
    third_center = third.frame_center.copy()

    array.swap(1, 3)

    assert array.values == ("c", "b", "a")
    assert array.iter_cells() == (third, second, first)
    assert [cell.index for cell in array.iter_cells()] == [3, 2, 1]
    assert np.allclose(first.frame_center, third_center)
    assert np.allclose(third.frame_center, first_center)


def test_append_matches_scaled_cell_geometry_and_keeps_label_stable() -> None:
    array = Array(["a", "b"], label="A:", show_indices=True)
    array.scale(4 / 5)
    label = array.label_mobject
    assert label is not None
    label_center = label.get_center().copy()
    width = array.cell(0).frame.width
    height = array.cell(0).frame.height

    array.append("c")

    new_cell = array.cell(2)
    assert new_cell.frame.width == pytest.approx(width)
    assert new_cell.frame.height == pytest.approx(height)
    assert np.allclose(label.get_center(), label_center)


def test_append_animation_keeps_label_stable_during_setup() -> None:
    array = Array(["a", "b"], label="A:", show_indices=True)
    label = array.label_mobject
    assert label is not None
    label_center = label.get_center().copy()

    array.animate_append("c")

    assert np.allclose(label.get_center(), label_center)


def test_swap_animation_cleanup_swaps_cells() -> None:
    array = Array(["a", "b", "c"], show_indices=True, start_index=1)
    first, second, third = array.iter_cells()
    anim = array.animate_swap(1, 3)

    anim.begin()
    anim.clean_up_from_scene(cast(Any, _SceneStub()))

    assert array.iter_cells() == (third, second, first)
    assert array.values == ("c", "b", "a")


def test_pointer_tracks_target_cell() -> None:
    array = Array(["a", "b"], show_indices=True)
    pointer = ArrayPointer(array, 0, label="i")
    before = pointer.arrow.get_center().copy()

    pointer.set_index(1)

    assert pointer.index == 1
    assert not np.allclose(pointer.arrow.get_center(), before)
    assert pointer.arrow.get_center()[0] > before[0]


def test_animation_cleanup_updates_value_semantics() -> None:
    array = Array(["a", "b"], show_indices=True)
    anim = array.animate_set_value(1, "z")

    anim.begin()
    anim.clean_up_from_scene(cast(Any, _SceneStub()))

    assert array.values == ("a", "z")


def test_remove_animation_cleanup_removes_faded_cell() -> None:
    array = Array(["a", "b", "c"], show_indices=True)
    anim = array.animate_remove(1)
    removed = array.submobjects[-1]

    assert array.values == ("a", "c")
    assert len(array.cells) == 2
    assert removed in array.submobjects

    anim.begin()
    anim.clean_up_from_scene(cast(Any, _SceneStub()))

    assert len(array.cells) == 2
    assert removed not in array.submobjects
