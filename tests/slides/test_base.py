"""SimplexScene cue recording and chrome helpers."""

from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("manim")

from simplex.manifest import SceneCueManifest
from simplex.section import CueKind, SimplexSectionType
from simplex.slides.base import _pretty_class_name, _SimplexSceneMixin


class _FakeBase:
    def __init__(self) -> None:
        self.time = 0.0
        self.waits: list[float] = []
        self.added: list[Any] = []
        self.renderer = type("Renderer", (), {"num_plays": 0})()

    def setup(self) -> None:
        pass

    def tear_down(self) -> None:
        pass

    def wait(self, duration: float) -> None:
        self.waits.append(duration)
        self.time += duration

    def add(self, *mobjects: Any) -> None:
        self.added.extend(mobjects)


class _FakeScene(_SimplexSceneMixin, _FakeBase):
    pass


def test_pretty_class_name_splits_capital_runs() -> None:
    assert _pretty_class_name("DFSLecture") == "DFS Lecture"
    assert _pretty_class_name("ImplementBFSSlide") == "Implement BFS Slide"
    assert _pretty_class_name("Section2Intro") == "Section2 Intro"


def test_slide_and_fragment_record_cues_with_padding() -> None:
    scene = _FakeScene()
    scene.setup()

    scene.slide("intro", title="Intro")
    scene.time = 1.0
    scene.fragment("detail", title="Detail")
    scene.time = 2.0
    scene.tear_down()

    assert [cue.id for cue in scene._simplex_cues] == ["intro", "detail"]
    assert [cue.kind for cue in scene._simplex_cues] == [CueKind.SLIDE, CueKind.FRAGMENT]
    assert scene._simplex_cues[0].end == pytest.approx(1.1)
    assert scene._simplex_cues[1].end == pytest.approx(2.1)
    assert scene.waits == [0.1, 0.1]


def test_auto_cue_ids_use_main_slide_title_and_number() -> None:
    scene = _FakeScene()
    scene.setup()

    scene.slide(title="Intro")
    scene.time = 1.0
    scene.fragment(title="Detail")
    scene.time = 2.0
    scene.slide(title="Intro")
    scene.time = 3.0
    scene.tear_down()

    assert [cue.id for cue in scene._simplex_cues] == [
        "intro",
        "intro-2",
        "intro-3",
    ]


def test_next_slide_alias_records_simplex_cues_only() -> None:
    scene = _FakeScene()
    scene.setup()

    scene.next_slide(name="Intro")
    scene.time = 1.0
    scene.next_slide()
    scene.time = 2.0
    scene.next_slide(section_type=SimplexSectionType.SUB_LOOP)
    scene.time = 3.0
    scene.tear_down()

    assert [cue.kind for cue in scene._simplex_cues] == [
        CueKind.SLIDE,
        CueKind.FRAGMENT,
        CueKind.LOOP,
    ]


def test_setup_chrome_noops_without_header_or_footer() -> None:
    scene = _FakeScene()
    scene.setup()
    original = scene.region

    chrome = scene.setup_chrome()

    assert chrome is None
    assert scene.region is original
    assert scene.canvas == {}


def test_writes_scene_cue_manifest(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SIMPLEX_CUES_DIR", str(tmp_path))
    scene = _FakeScene()
    scene.setup()

    scene.slide("intro", title="Intro")
    scene.time = 1.0
    scene.tear_down()

    manifest = SceneCueManifest.read(tmp_path / "_FakeScene.json")
    assert manifest.scene == "_FakeScene"
    assert manifest.cues[0].id == "intro"
