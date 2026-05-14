"""Theme tokens -- immutability, preset values, context push/pop."""

import pytest
from pydantic import ValidationError

from simplex.theme import presets
from simplex.theme.context import active_theme, get_active_theme


def test_dastimator_palette_background() -> None:
    assert presets.DASTIMATOR_DARK.palette.background == "#242424"


def test_definition_environment_seeded_from_dastimator() -> None:
    assert presets.DASTIMATOR_DARK.latex.environments["definition"] == "{minipage}{8cm}"


def test_preamble_contains_compact_display() -> None:
    preamble = presets.DASTIMATOR_DARK.latex.preamble
    assert "abovedisplayskip" in preamble
    assert "belowdisplayskip" in preamble


def test_palette_frozen() -> None:
    with pytest.raises(ValidationError):
        presets.DASTIMATOR_DARK.palette.background = "#000000"  # type: ignore[misc]


def test_theme_frozen() -> None:
    with pytest.raises(ValidationError):
        presets.DASTIMATOR_DARK.name = "other"  # type: ignore[misc]


def test_context_push_pop_restores_default() -> None:
    assert get_active_theme() is presets.DASTIMATOR_DARK
    with active_theme(presets.ACADEMIC_LIGHT) as t:
        assert get_active_theme() is t
    assert get_active_theme() is presets.DASTIMATOR_DARK


def test_presets_get_unknown_raises() -> None:
    with pytest.raises(KeyError):
        presets.get("nope")
