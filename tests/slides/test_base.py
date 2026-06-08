"""Slide section-type resolution -- auto-promotion to MAIN on first call.

Tests the ``_resolve_section_type`` method directly via a minimal stub
holding the only state it reads (``_current_main``). This isolates the
resolution logic from manim-slides' ``Slide`` machinery (no Scene init,
no renderer, no file output).
"""

from types import SimpleNamespace
from typing import Any

import pytest

pytest.importorskip("manim")
pytest.importorskip("manim_slides")

from manim import config as manim_config

from simplex.engine.region import Region
from simplex.section import SimplexSectionType
from simplex.slides.base import Slide, _pretty_class_name, _SimplexSlideMixin


class _MiniSlide:
    """Holds ``_current_main`` and borrows Slide's resolver."""

    _resolve_section_type = Slide._resolve_section_type

    def __init__(self) -> None:
        self._current_main: str | None = None


class _ChromeSlide:
    setup_chrome = Slide.setup_chrome

    def __init__(self) -> None:
        self.header = None
        self.footer = None
        self.chrome_kwargs = {}
        self.region = Region.full_frame()
        self.canvas: dict[str, Any] = {}
        self.mobjects: list[Any] = []

    def add_to_canvas(self, **mobjects: Any) -> None:
        self.canvas.update(mobjects)

    def add(self, *mobjects: Any) -> None:
        self.mobjects.extend(mobjects)


class _ForwardingBase:
    """Minimal super-class stub for exercising the full ``next_slide`` path."""

    def __init__(self, *, current_animation: int = 1, start_animation: int = 0) -> None:
        self._current_animation = current_animation
        self._start_animation = start_animation
        self._current_main: str | None = None
        self._wait_time_between_slides = 0.1
        self.renderer: Any = None
        self.events: list[tuple[str, Any]] = []

    @property
    def wait_time_between_slides(self) -> float:
        return self._wait_time_between_slides

    @wait_time_between_slides.setter
    def wait_time_between_slides(self, wait_time: float) -> None:
        self._wait_time_between_slides = max(wait_time, 0.0)

    def wait(self, duration: float) -> None:
        self.events.append(("wait", duration))
        self._current_animation += 1

    def next_slide(self, **kwargs: Any) -> None:
        self.events.append(
            (
                "next_slide",
                {
                    "kwargs": kwargs,
                    "wait_time_between_slides": self.wait_time_between_slides,
                },
            )
        )

    def tear_down(self) -> None:
        self.events.append(("tear_down", None))


class _ForwardingSlide(_SimplexSlideMixin, _ForwardingBase):
    pass


def _resolve(
    stub: _MiniSlide,
    name: str | None,
    section_type: SimplexSectionType | str | None = None,
    loop: bool = False,
) -> SimplexSectionType:
    return stub._resolve_section_type(name, section_type, loop)


def test_named_call_emits_main() -> None:
    stub = _MiniSlide()
    assert _resolve(stub, "Theorem") is SimplexSectionType.MAIN


def test_named_call_with_loop_emits_main_loop() -> None:
    stub = _MiniSlide()
    assert _resolve(stub, "Theorem", loop=True) is SimplexSectionType.MAIN_LOOP


def test_bare_first_call_auto_promotes_to_main() -> None:
    """First bare call -> MAIN. The forward path names it after the class."""
    stub = _MiniSlide()
    assert _resolve(stub, None) is SimplexSectionType.MAIN


def test_bare_first_call_with_loop_auto_promotes_to_main_loop() -> None:
    stub = _MiniSlide()
    assert _resolve(stub, None, loop=True) is SimplexSectionType.MAIN_LOOP


def test_bare_call_after_named_emits_sub() -> None:
    stub = _MiniSlide()
    stub._current_main = "Theorem"
    assert _resolve(stub, None) is SimplexSectionType.SUB


def test_bare_call_after_named_with_loop_emits_sub_loop() -> None:
    stub = _MiniSlide()
    stub._current_main = "Theorem"
    assert _resolve(stub, None, loop=True) is SimplexSectionType.SUB_LOOP


def test_explicit_section_type_overrides_inference() -> None:
    stub = _MiniSlide()
    out = _resolve(stub, "Title", section_type=SimplexSectionType.SUB_SKIP)
    assert out is SimplexSectionType.SUB_SKIP


def test_explicit_section_type_as_string_works() -> None:
    stub = _MiniSlide()
    out = _resolve(stub, "Title", section_type="simplex.main.skip")
    assert out is SimplexSectionType.MAIN_SKIP


def test_explicit_sub_section_type_before_any_main_still_honored() -> None:
    """An explicit section_type kwarg short-circuits the auto-promotion path."""
    stub = _MiniSlide()
    out = _resolve(stub, None, section_type=SimplexSectionType.SUB)
    assert out is SimplexSectionType.SUB


def test_pretty_class_name_splits_capital_runs() -> None:
    """Auto-promoted slide names get spaces between PascalCase boundaries."""
    assert _pretty_class_name("DFSLecture") == "DFS Lecture"
    assert _pretty_class_name("ImplementBFSSlide") == "Implement BFS Slide"
    assert _pretty_class_name("Title") == "Title"
    assert _pretty_class_name("HelloSlide") == "Hello Slide"
    assert _pretty_class_name("BFS") == "BFS"
    # Digit/uppercase boundaries also get a space.
    assert _pretty_class_name("Section2Intro") == "Section2 Intro"


def test_setup_chrome_noops_without_header_or_footer() -> None:
    stub = _ChromeSlide()
    original = stub.region

    chrome = stub.setup_chrome()

    assert chrome is None
    assert stub.region is original
    assert stub.canvas == {}


def test_setup_chrome_adds_canvas_and_updates_region() -> None:
    stub = _ChromeSlide()

    chrome = stub.setup_chrome(footer="foot")

    assert chrome is not None
    assert "footer" in stub.canvas
    assert stub.canvas["footer"] in stub.mobjects
    assert stub.region.bottom > Region.full_frame().bottom


def test_simplex_slides_skip_reverse_video_generation() -> None:
    assert Slide.skip_reversing is True


def test_next_slide_pads_current_slide_before_forwarding() -> None:
    stub = _ForwardingSlide(current_animation=2, start_animation=1)

    stub.next_slide(name="Intro")

    assert stub.events[0] == ("wait", 0.1)
    forwarded_name, forwarded = stub.events[1]
    assert forwarded_name == "next_slide"
    assert forwarded["kwargs"]["name"] == "Intro"
    assert forwarded["kwargs"]["section_type"] == SimplexSectionType.MAIN.value
    assert forwarded["kwargs"]["direction"] == "horizontal"
    assert forwarded["wait_time_between_slides"] == 0.0
    assert stub.wait_time_between_slides == 0.1


def test_next_slide_does_not_pad_empty_boundaries() -> None:
    stub = _ForwardingSlide(current_animation=4, start_animation=4)

    stub.next_slide(name="Intro")

    assert [event[0] for event in stub.events] == ["next_slide"]


def test_next_slide_suppresses_padding_after_partial_render_limit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(manim_config, "upto_animation_number", 0)
    stub = _ForwardingSlide(current_animation=2, start_animation=1)
    stub.renderer = SimpleNamespace(num_plays=1)

    stub.next_slide(name="Intro")

    forwarded_name, forwarded = stub.events[0]
    assert forwarded_name == "next_slide"
    assert forwarded["wait_time_between_slides"] == 0.0


def test_tear_down_pads_final_slide_before_forwarding() -> None:
    stub = _ForwardingSlide(current_animation=2, start_animation=1)

    stub.tear_down()

    assert stub.events == [("wait", 0.1), ("tear_down", None)]
    assert stub.wait_time_between_slides == 0.1


def test_tear_down_does_not_pad_empty_final_slide() -> None:
    stub = _ForwardingSlide(current_animation=4, start_animation=4)

    stub.tear_down()

    assert stub.events == [("tear_down", None)]


def test_tear_down_suppresses_padding_after_partial_render_limit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(manim_config, "upto_animation_number", 0)
    stub = _ForwardingSlide(current_animation=2, start_animation=1)
    stub.renderer = SimpleNamespace(num_plays=1)

    stub.tear_down()

    assert stub.events == [("tear_down", None)]
