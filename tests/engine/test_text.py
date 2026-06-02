"""``Caption`` / ``TexPage`` pick up theme defaults at construction."""

import pytest

pytest.importorskip("manim")

from manim import LARGE_BUFF

from simplex.engine.defaults import apply_theme_defaults
from simplex.engine.region import Region
from simplex.engine.text import Caption, TexPage, minipage_cm_for_page_width
from simplex.theme import presets
from simplex.theme.context import active_theme


def test_caption_uses_caption_font_size() -> None:
    with active_theme(presets.SIMPLEX_DARK) as theme:
        mob = Caption("hi")
        assert mob.font_size == theme.typography.caption


def test_tex_page_default_width_uses_full_frame_minus_buff() -> None:
    with active_theme(presets.SIMPLEX_DARK) as theme:
        mob = TexPage("body")
        usable_width = Region.full_frame().width - 2 * LARGE_BUFF
        expected = minipage_cm_for_page_width(usable_width, font_size=theme.typography.body)
        assert mob.minipage_width_cm == pytest.approx(expected)
        assert mob.page_buff == LARGE_BUFF
        assert mob.tex_environment == f"{{minipage}}{{{expected}cm}}"


def test_tex_page_page_width_number_sets_minipage_from_manim_units() -> None:
    with active_theme(presets.SIMPLEX_DARK) as theme:
        mob = TexPage("body", page_width=10.5, buff=0.25)
        expected = minipage_cm_for_page_width(10.0, font_size=theme.typography.body)
        assert mob.page_width_munits == pytest.approx(10.5)
        assert mob.minipage_width_cm == pytest.approx(expected)


def test_tex_page_page_width_accepts_region() -> None:
    region = Region(top=1.0, bottom=-1.0, left=-2.0, right=3.0)

    with active_theme(presets.SIMPLEX_DARK) as theme:
        mob = TexPage("body", page_width=region, buff=0.5)
        expected = minipage_cm_for_page_width(region.width - 1.0, font_size=theme.typography.body)
        assert mob.page_width_munits == pytest.approx(region.width)
        assert mob.minipage_width_cm == pytest.approx(expected)


def test_tex_page_subclass_class_attrs_override_defaults() -> None:
    class WidePage(TexPage):
        page_width = 12.0
        buff = 0.25

    with active_theme(presets.SIMPLEX_DARK) as theme:
        mob = WidePage("body")
        expected = minipage_cm_for_page_width(11.5, font_size=theme.typography.body)
        assert mob.minipage_width_cm == pytest.approx(expected)


def test_tex_page_kwarg_wins_over_subclass_attr() -> None:
    class WidePage(TexPage):
        page_width = 12.0

    with active_theme(presets.SIMPLEX_DARK) as theme:
        mob = WidePage("body", page_width=6.5, buff=0.25)
        expected = minipage_cm_for_page_width(6.0, font_size=theme.typography.body)
        assert mob.minipage_width_cm == pytest.approx(expected)


def test_tex_page_rejects_removed_width_cm_kwarg() -> None:
    with active_theme(presets.SIMPLEX_DARK), pytest.raises(TypeError, match="page_width"):
        TexPage("body", width_cm=10.5)


def test_tex_page_math_spacing_sets_display_skip_lengths() -> None:
    with active_theme(presets.SIMPLEX_DARK):
        mob = TexPage("body", math_spacing=3)

    first_part = mob.tex_strings[0]
    assert r"\setlength{\abovedisplayskip}{3pt}" in first_part
    assert r"\setlength{\belowdisplayskip}{3pt}" in first_part
    assert r"\setlength{\abovedisplayshortskip}{3pt}" in first_part
    assert r"\setlength{\belowdisplayshortskip}{3pt}" in first_part


def test_tex_page_splits_display_equations_for_direct_access() -> None:
    with active_theme(presets.SIMPLEX_DARK):
        mob = TexPage(r"before \[x=1\] middle \[y=2\] after")

    assert mob.equation_part_indices == (1, 3)
    assert mob.part_roles == ("text", "equation", "text", "equation", "text")
    assert mob.equation(0) is mob[1]
    assert mob.equation(1) is mob[3]


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
