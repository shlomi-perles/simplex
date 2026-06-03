"""Outline progress bar geometry."""

import numpy as np
import pytest

pytest.importorskip("manim")

from manim import RIGHT

from simplex.engine.region import Region
from simplex.mobjects.outline import OutlineProgressBar
from simplex.slides.outline import OutlineScene
from simplex.theme.context import active_theme
from simplex.theme.presets import SIMPLEX_DARK


def test_progress_bar_from_region_uses_linspace_defaults() -> None:
    region = Region(top=2.0, bottom=0.0, left=0.0, right=4.0)
    bar = OutlineProgressBar.from_region(region, 3)

    expected = region.linspace(RIGHT, 3)
    centers = [dot.get_center() for dot in bar.dots]
    for actual, point in zip(centers, expected, strict=True):
        assert np.allclose(actual, point)


def test_progress_bar_y_override_only_changes_orthogonal_coordinate() -> None:
    region = Region(top=2.0, bottom=0.0, left=0.0, right=4.0)
    bar = OutlineProgressBar.from_region(region, 3, y=-1.5)

    expected = region.linspace(RIGHT, 3, orthogonal=-1.5)
    centers = [dot.get_center() for dot in bar.dots]
    for actual, point in zip(centers, expected, strict=True):
        assert np.allclose(actual, point)


def test_progress_bar_set_index_moves_active_dot() -> None:
    region = Region(top=2.0, bottom=0.0, left=0.0, right=4.0)
    bar = OutlineProgressBar.from_region(region, 3)

    bar.set_index(2)

    assert bar.active_index == 2
    assert np.allclose(bar.moving_dot.get_center(), bar.dots[2].get_center())
    assert bar.completed_track.get_stroke_opacity() == pytest.approx(1.0)


def test_progress_bar_track_uses_theme_foreground_not_graph_edge() -> None:
    theme = SIMPLEX_DARK.model_copy(
        update={
            "palette": SIMPLEX_DARK.palette.model_copy(
                update={"font": "#101010", "edge": "#FF00FF"}
            )
        }
    )
    region = Region(top=2.0, bottom=0.0, left=0.0, right=4.0)

    with active_theme(theme):
        bar = OutlineProgressBar.from_region(region, 3)

    assert bar.track_color == "#101010"
    stroke_color = bar.track.get_stroke_color()
    assert stroke_color is not None
    assert stroke_color.to_hex() == "#101010"


class _MiniOutline:
    make_progress_bar = OutlineScene.make_progress_bar
    _progress_bar_y = OutlineScene._progress_bar_y

    def __init__(self) -> None:
        self.region = Region(top=2.0, bottom=0.0, left=0.0, right=4.0)
        self.part_count = 3
        self.progress_y = 0.25


def test_outline_scene_progress_bar_uses_scene_region_linspace() -> None:
    mini = _MiniOutline()
    bar = mini.make_progress_bar()

    expected_y = mini.region.bottom + mini.region.height * mini.progress_y
    expected = mini.region.linspace(RIGHT, mini.part_count, orthogonal=expected_y)
    centers = [dot.get_center() for dot in bar.dots]
    for actual, point in zip(centers, expected, strict=True):
        assert np.allclose(actual, point)
