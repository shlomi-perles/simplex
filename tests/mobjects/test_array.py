"""Array mobject construction and state semantics."""

from typing import Any, cast

import numpy as np
import pytest

pytest.importorskip("manim")

from manim import RIGHT

import simplex
from simplex.engine.region import Region
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


def test_swap_exchanges_values_not_slots_or_indices() -> None:
    array = Array(["a", "b", "c"], show_indices=True, start_index=1)
    centers = [cell.frame_center.copy() for cell in array.iter_cells()]

    array.swap(1, 3)

    assert array.values == ("c", "b", "a")
    assert [cell.index for cell in array.iter_cells()] == [1, 2, 3]
    for cell, center in zip(array.iter_cells(), centers, strict=True):
        assert np.allclose(cell.frame_center, center)


def test_pointer_tracks_target_cell() -> None:
    array = Array(["a", "b"], show_indices=True)
    pointer = ArrayPointer(array, 0, label="i")
    before = pointer.arrow.get_center().copy()

    pointer.set_index(1)

    assert pointer.index == 1
    assert not np.allclose(pointer.arrow.get_center(), before)
    assert pointer.arrow.get_center()[0] > before[0]


def test_from_region_places_array_inside_region() -> None:
    region = Region(top=2.0, bottom=-2.0, left=-3.0, right=3.0)
    array = Array.from_region(region, ["x", "y"], anchor=RIGHT, buff=0.2)

    assert array.get_right()[0] <= region.right - 0.2 + 1e-6


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
