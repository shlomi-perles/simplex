"""Theme defaults for vanilla Manim mobjects."""

import pytest

pytest.importorskip("manim")

from manim import DecimalNumber, Integer, MarkupText, Paragraph, Variable
from manim.utils.color import ManimColor

from simplex.engine.defaults import apply_theme_defaults
from simplex.engine.dynamics import DN
from simplex.theme.presets import SIMPLEX_DARK, SIMPLEX_LIGHT


def _drawn_colors(mob) -> set[str]:
    return {
        submob.get_color().to_hex()
        for submob in mob.get_family()
        if not submob.submobjects and submob.get_all_points().size
    }


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
