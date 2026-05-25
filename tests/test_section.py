"""SimplexSectionType -- string values, is_main/is_sub/is_loop/is_skip predicates."""

from simplex.section import SimplexSectionType


def test_main_values_start_with_simplex_main() -> None:
    assert SimplexSectionType.MAIN.value == "simplex.main"
    assert SimplexSectionType.MAIN_LOOP.value == "simplex.main.loop"
    assert SimplexSectionType.MAIN_SKIP.value == "simplex.main.skip"


def test_sub_values_start_with_simplex_sub() -> None:
    assert SimplexSectionType.SUB.value == "simplex.sub"
    assert SimplexSectionType.SUB_LOOP.value == "simplex.sub.loop"
    assert SimplexSectionType.SUB_SKIP.value == "simplex.sub.skip"


def test_is_main_predicate() -> None:
    assert SimplexSectionType.MAIN.is_main
    assert SimplexSectionType.MAIN_LOOP.is_main
    assert SimplexSectionType.MAIN_SKIP.is_main
    assert not SimplexSectionType.SUB.is_main


def test_is_sub_predicate() -> None:
    assert SimplexSectionType.SUB.is_sub
    assert SimplexSectionType.SUB_LOOP.is_sub
    assert SimplexSectionType.SUB_SKIP.is_sub
    assert not SimplexSectionType.MAIN.is_sub


def test_is_loop_predicate() -> None:
    assert SimplexSectionType.MAIN_LOOP.is_loop
    assert SimplexSectionType.SUB_LOOP.is_loop
    assert not SimplexSectionType.MAIN.is_loop
    assert not SimplexSectionType.MAIN_SKIP.is_loop


def test_is_skip_predicate() -> None:
    assert SimplexSectionType.MAIN_SKIP.is_skip
    assert SimplexSectionType.SUB_SKIP.is_skip
    assert not SimplexSectionType.SUB.is_skip
    assert not SimplexSectionType.SUB_LOOP.is_skip


def test_round_trips_through_str() -> None:
    """StrEnum members compare equal to their string values, key for Manim section JSON."""
    assert SimplexSectionType.MAIN == "simplex.main"
    assert SimplexSectionType("simplex.sub.loop") == SimplexSectionType.SUB_LOOP


def test_module_imports_without_manim_in_clean_subprocess() -> None:
    """The reconcile / web pipelines rely on this module being Manim-free.

    Verified in a clean Python subprocess so other tests' imports don't
    pollute sys.modules. ``manim`` must not appear after importing
    ``simplex.section``.
    """
    import subprocess
    import sys

    script = (
        "import sys; "
        "import simplex.section; "  # the module under test
        "assert 'manim' not in sys.modules, "
        "f'manim leaked into simplex.section import; sys.modules subset: '"
        "f'{[m for m in sys.modules if m.startswith(\"manim\")]}'"
    )
    result = subprocess.run(  # noqa: S603 -- fixed script, fixed executable
        [sys.executable, "-c", script],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
