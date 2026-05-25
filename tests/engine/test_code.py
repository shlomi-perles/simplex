"""Style registration + HighlightResult shape + inline math helpers."""

import pytest

pytest.importorskip("pygments")

from simplex.engine.code import (
    HighlightResult,
    _glyph_positions,
    _glyph_span,
)
from simplex.theme.pygments_style import (
    SimplexPycharm,
    SimplexSolarizedLight,
    register_all_builtin_styles,
    register_style,
)


def test_register_style_adds_to_style_map() -> None:
    import pygments.styles

    register_style(SimplexPycharm)
    assert "simplex_pycharm" in pygments.styles.STYLE_MAP


def test_register_style_is_idempotent() -> None:
    register_style(SimplexPycharm)
    register_style(SimplexPycharm)
    register_style(SimplexPycharm)


def test_register_all_registers_both_styles() -> None:
    import pygments.styles

    register_all_builtin_styles()
    assert "simplex_pycharm" in pygments.styles.STYLE_MAP
    assert "simplex_solarized_light" in pygments.styles.STYLE_MAP


def test_simplex_pycharm_has_expected_background() -> None:
    assert SimplexPycharm.background_color == "#111111"


def test_simplex_solarized_light_has_expected_background() -> None:
    assert SimplexSolarizedLight.background_color == "#fffce4"


def test_highlight_result_iterates_fade_only_when_indicate_is_none() -> None:
    pytest.importorskip("manim")
    from manim import AnimationGroup

    result = HighlightResult(fade=AnimationGroup())
    assert list(result) == [result.fade]


def test_highlight_result_iterates_fade_then_indicate() -> None:
    pytest.importorskip("manim")
    from manim import AnimationGroup, Indicate, Square

    fade = AnimationGroup()
    ind = Indicate(Square())
    result = HighlightResult(fade=fade, indicate=ind)
    assert list(result) == [fade, ind]


def test_highlight_result_is_frozen() -> None:
    pytest.importorskip("manim")
    from dataclasses import FrozenInstanceError

    from manim import AnimationGroup

    result = HighlightResult(fade=AnimationGroup())
    with pytest.raises(FrozenInstanceError):
        result.indicate = None  # type: ignore[misc]


def test_glyph_positions_marks_whitespace_as_none() -> None:
    assert _glyph_positions("ab cd") == [0, 1, None, 2, 3]
    assert _glyph_positions("    x") == [None, None, None, None, 0]
    assert _glyph_positions("") == []
    assert _glyph_positions("\t  $x$") == [None, None, None, 0, 1, 2]


def test_glyph_positions_counts_dollar_signs_as_visible() -> None:
    # The marker characters DO render as glyphs in Manim's Code, so
    # they must be counted -- otherwise the span indices drift right.
    assert _glyph_positions("$x$") == [0, 1, 2]
    assert _glyph_positions("a $b$ c") == [0, None, 1, 2, 3, None, 4]


def test_glyph_span_for_dollar_delimited_region() -> None:
    positions = _glyph_positions("a $b$ c")
    # ``$b$`` spans source chars [2, 5) -> glyphs [1, 4).
    start, end = _glyph_span(positions, 2, 5)
    assert (start, end) == (1, 4)


def test_glyph_span_skips_leading_whitespace() -> None:
    positions = _glyph_positions("    $x$")
    # Indent is whitespace; the first glyph is the opening ``$``.
    start, end = _glyph_span(positions, 4, 7)
    assert (start, end) == (0, 3)


def test_glyph_span_returns_none_for_all_whitespace_slice() -> None:
    positions = _glyph_positions("  abc")
    start, end = _glyph_span(positions, 0, 2)
    assert start is None
    assert end is None


def test_inline_math_in_code_is_noop_when_no_dollar_signs() -> None:
    pytest.importorskip("manim")
    from simplex.engine.code import code_block, inline_math_in_code

    block = code_block("x = 1\ny = 2", language="python")
    width_before = block.width
    inline_math_in_code(block, "x = 1\ny = 2")
    assert block.width == pytest.approx(width_before)


def test_code_with_math_returns_a_manim_code() -> None:
    pytest.importorskip("manim")
    from manim import Code

    from simplex.engine.code import code_with_math

    block = code_with_math("x = $1$", language="python")
    assert isinstance(block, Code)
    assert len(block.code_lines) == 1


def test_code_with_math_preserves_background_padding() -> None:
    pytest.importorskip("manim")
    from simplex.engine.code import code_with_math

    block = code_with_math(
        "for i in $1..n$:\n    print($i$)",
        language="python",
        paragraph_config={"font": "Monospace"},
    )
    # ``Code`` defaults to ``buff=0.3``; the refit must keep that buff so
    # the inline-math block visually matches a plain ``code_block``.
    bg = block.background
    inner_height = max(m.height for m in block.submobjects if m is not bg)
    inner_width = max(m.width for m in block.submobjects if m is not bg)
    assert bg.height >= inner_height
    assert bg.width >= inner_width
    assert bg.buff == pytest.approx(0.3)


def test_code_with_math_bold_wraps_with_boldsymbol() -> None:
    # We can't easily inspect MathTex source post-construction, but we
    # can at least verify the helper accepts the flag without error and
    # returns a Code with the same number of code lines.
    pytest.importorskip("manim")
    from simplex.engine.code import code_with_math

    block = code_with_math("x = $a + b$", language="python", bold_math=True)
    assert len(block.code_lines) == 1
