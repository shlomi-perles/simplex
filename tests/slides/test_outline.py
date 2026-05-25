"""OutlineScene control-flow smoke tests."""

from typing import Any, cast

import pytest

pytest.importorskip("manim")
pytest.importorskip("manim_slides")

import numpy as np
from manim import (
    DEFAULT_MOBJECT_TO_EDGE_BUFFER,
    Circle,
    Group,
    Rectangle,
    Square,
    Tex,
    config,
)

from simplex.slides.outline import OutlinePart, OutlineScene
from simplex.theme.context import get_active_theme


class _Outline(OutlineScene):
    def __init__(self, *, focus_index: int | None = None, **kwargs: Any) -> None:
        super().__init__(
            parts=[
                OutlinePart(title=Circle(), label=Circle(), visual=Square()),
                OutlinePart(title=Circle(), label=Circle(), visual=Square()),
            ],
            focus_index=focus_index,
            **kwargs,
        )


def _prepare_geometry(scene: OutlineScene) -> None:
    scene.setup()
    scene.progress_bar = scene.make_progress_bar()
    scene.compact_mobjects = Group()
    scene.initial_mobjects = Group(scene.progress_bar)


def _stub_timeline(scene: OutlineScene) -> None:
    def noop(*args: Any, **kwargs: Any) -> None:
        return None

    target = cast(Any, scene)
    target.play = noop
    target.wait = noop
    target.next_slide = noop


def test_outline_scene_constructs_full_flow_without_renderer_writes() -> None:
    scene = _Outline()
    scene.setup()
    _stub_timeline(scene)

    scene.construct()

    assert scene.current_index == scene.part_count


def test_outline_scene_constructs_focused_flow_without_renderer_writes() -> None:
    scene = _Outline(focus_index=1)
    scene.setup()
    _stub_timeline(scene)

    scene.construct()

    assert scene.outline_started
    assert scene.focus_index == 1


def test_visual_title_uses_frame_top_edge() -> None:
    title = Tex("Large outline title", font_size=24)
    scene = OutlineScene([OutlinePart(title=title, label=Square(), visual=Square())])
    _prepare_geometry(scene)

    scene._place_title(scene.parts[0])

    expected_top = config.frame_y_radius - DEFAULT_MOBJECT_TO_EDGE_BUFFER
    assert title.get_top()[1] == pytest.approx(expected_top)
    assert title.font_size == pytest.approx(get_active_theme().typography.h1)


def test_labels_fit_bottom_region_and_share_font_size() -> None:
    parts = [
        OutlinePart(title=Square(), label=Tex("Short", font_size=48), visual=Square()),
        OutlinePart(
            title=Square(),
            label=Tex(r"A much much longer label", font_size=48),
            visual=Square(),
        ),
    ]
    scene = OutlineScene(parts)
    _prepare_geometry(scene)

    for index, part in enumerate(parts):
        scene._place_label(index, part.label)

    label_region = scene._label_region()
    max_label_width = scene.progress_bar.spacing * 0.9 - 0.4
    max_label_height = label_region.height - 0.4
    for index, part in enumerate(parts):
        label = part.label
        assert label.width <= max_label_width + 1e-6
        assert label.height <= max_label_height + 1e-6
        assert label.get_center()[0] == pytest.approx(scene.dots[index].get_center()[0])
        assert label.get_center()[1] == pytest.approx(label_region.center[1])

    assert parts[0].label.font_size == pytest.approx(parts[1].label.font_size)


def test_feature_visual_fits_region_above_compact_thumbnail() -> None:
    parts = [
        OutlinePart(
            title=Square(),
            label=Square(),
            visual=Rectangle(width=0.2, height=3.0),
        ),
        OutlinePart(title=Square(), label=Square(), visual=Square(side_length=10.0)),
    ]
    scene = OutlineScene(parts)
    _prepare_geometry(scene)

    previous_visual = parts[0].visual
    assert previous_visual is not None
    scene._place_thumbnail(0, previous_visual, parts[0].thumbnail_scale)
    scene._remember_compact(previous_visual)

    current = parts[1]
    assert current.visual is not None
    scene._place_title(current)
    scene._place_feature_visual(current.visual, current, exclude_compact=current.visual)
    feature_region = scene._feature_region(current, exclude_compact=current.visual)

    assert feature_region.bottom >= previous_visual.get_top()[1]
    assert current.visual.width <= feature_region.width + 1e-6
    assert current.visual.height <= feature_region.height + 1e-6
    assert np.allclose(current.visual.get_center(), feature_region.center)
