"""Theme tokens -- immutability, preset values, context push/pop."""

import pytest
from pydantic import ValidationError

from simplex.theme import presets
from simplex.theme.context import active_theme, get_active_theme, set_default_theme
from simplex.theme.pygments_style import background_color_for_style
from simplex.theme.styles.simplex_pycharm import SimplexPycharm
from simplex.theme.styles.simplex_solarized_light import SimplexSolarizedLight


def test_simplex_palette_background() -> None:
    assert presets.SIMPLEX_DARK.palette.background == "#242424"


def test_simplex_latex_has_no_legacy_environments() -> None:
    """The ``{minipage}{20cm}`` env moved from the theme into ``TexPage`` --
    the LaTeX profile no longer carries it. Tests guard against regression
    that would split the same magic string across multiple sources again.
    """
    assert "definition" not in presets.SIMPLEX_DARK.latex.environments


def test_chrome_buffs_have_sensible_defaults() -> None:
    assert presets.SIMPLEX_DARK.spacing.header_buff > 0
    assert presets.SIMPLEX_DARK.spacing.footer_buff > 0


def test_preamble_contains_compact_display() -> None:
    preamble = presets.SIMPLEX_DARK.latex.preamble
    assert "abovedisplayskip" in preamble
    assert "belowdisplayskip" in preamble


def test_palette_frozen() -> None:
    with pytest.raises(ValidationError):
        presets.SIMPLEX_DARK.palette.background = "#000000"  # type: ignore[misc]


def test_theme_frozen() -> None:
    with pytest.raises(ValidationError):
        presets.SIMPLEX_DARK.name = "other"  # type: ignore[misc]


def test_context_push_pop_restores_default() -> None:
    assert get_active_theme() is presets.SIMPLEX_DARK
    with active_theme(presets.SIMPLEX_LIGHT) as t:
        assert get_active_theme() is t
    assert get_active_theme() is presets.SIMPLEX_DARK


def test_default_theme_sets_fallback_without_breaking_context_override() -> None:
    try:
        set_default_theme(presets.SIMPLEX_LIGHT)
        assert get_active_theme() is presets.SIMPLEX_LIGHT
        with active_theme(presets.SIMPLEX_DARK):
            assert get_active_theme() is presets.SIMPLEX_DARK
        assert get_active_theme() is presets.SIMPLEX_LIGHT
    finally:
        set_default_theme(presets.SIMPLEX_DARK)


def test_presets_get_unknown_raises() -> None:
    with pytest.raises(KeyError):
        presets.get("nope")


def test_simplex_dark_uses_simplex_pycharm_code_style() -> None:
    assert presets.SIMPLEX_DARK.code_style is SimplexPycharm


def test_simplex_light_uses_solarized_light_code_style() -> None:
    assert presets.SIMPLEX_LIGHT.code_style is SimplexSolarizedLight


def test_code_theme_tokens_match_builtin_styles() -> None:
    assert presets.SIMPLEX_DARK.typography.mono_family == "JetBrains Mono"
    assert background_color_for_style(presets.SIMPLEX_DARK.code_style) == "#1A1A1A"
    assert presets.SIMPLEX_LIGHT.typography.mono_family == "JetBrains Mono"
    assert (
        background_color_for_style(presets.SIMPLEX_LIGHT.code_style)
        == SimplexSolarizedLight.background_color
    )


def test_code_style_defaults_to_simplex_pycharm() -> None:
    from simplex.theme.tokens import Palette, Theme

    theme = Theme(
        name="test",
        palette=Palette(
            background="#000",
            font="#fff",
            accent="#fff",
            vertex="#fff",
            vertex_stroke="#fff",
            edge="#fff",
            weight="#fff",
            visited="#fff",
            label="#fff",
            distance="#fff",
        ),
    )
    assert theme.code_style is SimplexPycharm
