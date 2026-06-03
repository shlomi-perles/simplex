"""Theme defaults for vanilla Manim mobjects."""

import pytest

pytest.importorskip("manim")

import manim
from manim import (
    DEFAULT_STROKE_WIDTH,
    Arrow,
    DecimalNumber,
    Integer,
    Line,
    MarkupText,
    Mobject,
    Paragraph,
    Rectangle,
    Square,
    Variable,
    VMobject,
)
from manim.utils.color import ManimColor

from simplex.engine.defaults import apply_theme_defaults, code_theme_defaults
from simplex.engine.dynamics import DN
from simplex.theme.presets import SIMPLEX_DARK, SIMPLEX_LIGHT


def _drawn_colors(mob: Mobject) -> set[str]:
    return {
        submob.get_color().to_hex()
        for submob in mob.get_family()
        if not submob.submobjects and submob.get_all_points().size
    }


def _stroke_color_hex(mob: VMobject) -> str:
    color = mob.get_stroke_color()
    assert color is not None
    return color.to_hex()


def test_apply_theme_defaults_updates_number_mobjects() -> None:
    expected = ManimColor(SIMPLEX_LIGHT.palette.font).to_hex()

    try:
        apply_theme_defaults(SIMPLEX_LIGHT)
        decimal = DecimalNumber(1.23)
        integer = Integer(7)
        variable = Variable(1.23, "x")
        dynamic = DN(lambda: 1.23)

        assert decimal.get_color().to_hex() == expected
        assert integer.get_color().to_hex() == expected
        assert variable.get_color().to_hex() == expected
        assert variable.value.get_color().to_hex() == expected
        assert dynamic.get_color().to_hex() == expected
        assert decimal.font_size == pytest.approx(SIMPLEX_LIGHT.typography.body)
        assert integer.font_size == pytest.approx(SIMPLEX_LIGHT.typography.body)
        assert dynamic.font_size == pytest.approx(SIMPLEX_LIGHT.typography.body)
        assert _drawn_colors(decimal) == {expected}
        assert _drawn_colors(integer) == {expected}
        assert _drawn_colors(variable.label) == {expected}
        assert _drawn_colors(variable.value) == {expected}
    finally:
        apply_theme_defaults(SIMPLEX_DARK)


def test_apply_theme_defaults_updates_non_text_subclasses() -> None:
    expected = ManimColor(SIMPLEX_LIGHT.palette.font).to_hex()

    try:
        apply_theme_defaults(SIMPLEX_LIGHT)
        markup = MarkupText("value")
        paragraph = Paragraph("value", "more")

        assert _drawn_colors(markup) == {expected}
        assert _drawn_colors(paragraph) == {expected}
    finally:
        apply_theme_defaults(SIMPLEX_DARK)


def test_apply_theme_defaults_keeps_vanilla_shape_strokes_on_theme_white() -> None:
    theme = SIMPLEX_LIGHT.model_copy(
        update={
            "palette": SIMPLEX_LIGHT.palette.model_copy(
                update={"font": "#101010", "edge": "#FF00FF"}
            )
        }
    )

    try:
        apply_theme_defaults(theme)
        expected = manim.WHITE.to_hex()
        line = Line()
        arrow = Arrow()
        rectangle = Rectangle()
        square = Square()

        assert _stroke_color_hex(line) == expected
        assert _stroke_color_hex(arrow) == expected
        assert _stroke_color_hex(rectangle) == expected
        assert _stroke_color_hex(square) == expected
        assert line.get_stroke_width() == pytest.approx(DEFAULT_STROKE_WIDTH)
    finally:
        apply_theme_defaults(SIMPLEX_DARK)


def test_apply_theme_defaults_omits_shape_overrides_for_builtin_white() -> None:
    try:
        apply_theme_defaults(SIMPLEX_LIGHT)
        apply_theme_defaults(SIMPLEX_DARK)
        assert _stroke_color_hex(Line()) == "#FFFFFF"
        assert _stroke_color_hex(Rectangle()) == "#FFFFFF"
    finally:
        apply_theme_defaults(SIMPLEX_DARK)


def test_code_background_uses_theme_white_not_font_or_graph_edge() -> None:
    theme = SIMPLEX_LIGHT.model_copy(
        update={
            "palette": SIMPLEX_LIGHT.palette.model_copy(
                update={"font": "#101010", "edge": "#FF00FF"}
            )
        }
    )

    _, _, background_config = code_theme_defaults(theme)

    stroke_color = background_config["stroke_color"]
    assert isinstance(stroke_color, ManimColor)
    assert stroke_color.to_hex() == manim.WHITE.to_hex()


def test_code_background_omits_stroke_color_for_builtin_white() -> None:
    _, _, background_config = code_theme_defaults(SIMPLEX_DARK)

    assert "stroke_color" not in background_config
