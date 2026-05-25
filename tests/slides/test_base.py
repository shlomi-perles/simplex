"""BaseSlide section-type resolution -- auto-promotion to MAIN on first call.

Tests the ``_resolve_section_type`` method directly via a minimal stub
holding the only state it reads (``_current_main``). This isolates the
resolution logic from manim-slides' ``Slide`` machinery (no Scene init,
no renderer, no file output).
"""

import pytest

pytest.importorskip("manim")
pytest.importorskip("manim_slides")

from simplex.section import SimplexSectionType
from simplex.slides.base import BaseSlide, _pretty_class_name


class _MiniSlide:
    """Holds ``_current_main`` and borrows BaseSlide's resolver."""

    _resolve_section_type = BaseSlide._resolve_section_type

    def __init__(self) -> None:
        self._current_main: str | None = None


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
