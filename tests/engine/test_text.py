"""``Caption`` / ``TexPage`` pick up theme defaults at construction."""

import pytest

pytest.importorskip("manim")

from simplex.engine.defaults import apply_theme_defaults
from simplex.engine.text import Caption, TexPage
from simplex.theme import presets
from simplex.theme.context import active_theme


def test_caption_uses_caption_font_size() -> None:
    with active_theme(presets.SIMPLEX_DARK) as theme:
        mob = Caption("hi")
        assert mob.font_size == theme.typography.caption


def test_tex_page_default_width_is_20cm() -> None:
    with active_theme(presets.SIMPLEX_DARK):
        mob = TexPage("body")
        assert mob.tex_environment == "{minipage}{20.0cm}"


def test_tex_page_width_cm_kwarg_overrides_default() -> None:
    with active_theme(presets.SIMPLEX_DARK):
        mob = TexPage("body", width_cm=10.5)
        assert mob.tex_environment == "{minipage}{10.5cm}"


def test_tex_page_subclass_class_attr_overrides_default() -> None:
    class WidePage(TexPage):
        width_cm = 12.0

    with active_theme(presets.SIMPLEX_DARK):
        mob = WidePage("body")
        assert mob.tex_environment == "{minipage}{12.0cm}"


def test_tex_page_kwarg_wins_over_subclass_attr() -> None:
    class WidePage(TexPage):
        width_cm = 12.0

    with active_theme(presets.SIMPLEX_DARK):
        mob = WidePage("body", width_cm=6.5)
        assert mob.tex_environment == "{minipage}{6.5cm}"


def test_plain_tex_picks_up_body_font_size_after_apply_defaults() -> None:
    """Once ``apply_theme_defaults`` runs, plain Tex carries body font size.

    Replaces the removed ``BodyText`` helper -- callers write ``Tex(...)``
    and inherit the body size for free (matching what the plugin does at
    import time via ``simplex.plugin:activate``).
    """
    from manim import Tex

    with active_theme(presets.SIMPLEX_DARK) as theme:
        apply_theme_defaults(theme)
        mob = Tex("hi")
        assert mob.font_size == theme.typography.body


def test_explicit_font_size_wins_over_theme_default() -> None:
    with active_theme(presets.SIMPLEX_DARK):
        mob = Caption("hi", font_size=12)
        assert mob.font_size == 12
