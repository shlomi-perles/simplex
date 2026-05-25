"""Web palette CSS emits tokens, not global page styles."""

from simplex.theme.styles.simplex_pycharm import SimplexPycharm
from simplex.theme.tokens import WebPalette
from simplex.theme.web_css import render_code_style_css, render_web_css


def test_render_web_css_is_variables_only() -> None:
    css = render_web_css(WebPalette(background="#123456"))

    assert "--simplex-bg: #123456" in css
    assert "body {" not in css
    assert ".reveal" not in css


def test_default_web_background_matches_portal_chrome() -> None:
    css = render_web_css(WebPalette())

    assert "--simplex-bg: #2b2b2b" in css


def test_render_web_css_includes_code_style_vars() -> None:
    css = render_web_css(WebPalette(), code_style=SimplexPycharm)

    assert "--simplex-code-bg: #111111" in css
    assert "--simplex-code-keyword: #CC7832" in css


def test_render_code_style_css_extracts_background() -> None:
    css = render_code_style_css(SimplexPycharm)

    assert "--simplex-code-bg: #111111" in css


def test_render_code_style_css_extracts_token_colors() -> None:
    css = render_code_style_css(SimplexPycharm)

    assert "--simplex-code-comment: #808080" in css
    assert "--simplex-code-string" in css
