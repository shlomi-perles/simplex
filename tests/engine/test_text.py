"""BodyText / Caption / Definition pick up theme defaults at construction."""

import pytest

pytest.importorskip("manim")

from simplex.engine.text import BodyText, Caption, Definition
from simplex.theme import presets
from simplex.theme.context import active_theme


def test_body_uses_body_font_size() -> None:
    with active_theme(presets.DASTIMATOR_DARK) as theme:
        mob = BodyText("hi")
        assert mob.font_size == theme.typography.body


def test_caption_uses_caption_font_size() -> None:
    with active_theme(presets.DASTIMATOR_DARK) as theme:
        mob = Caption("hi")
        assert mob.font_size == theme.typography.caption


def test_definition_uses_minipage_environment() -> None:
    with active_theme(presets.DASTIMATOR_DARK):
        mob = Definition("body")
        assert mob.tex_environment == "{minipage}{8cm}"


def test_explicit_font_size_wins_over_theme_default() -> None:
    with active_theme(presets.DASTIMATOR_DARK):
        mob = BodyText("hi", font_size=12)
        assert mob.font_size == 12
