"""Render a `WebPalette` to a `:root { --simplex-* }` CSS variables block.

Consumed by two surfaces:
- the portal `<head>` (homepage cards + section pages)
- per-deck RevealJS HTML `<head>` (slide chrome, captions)

This module intentionally emits custom properties only. Surface-specific
stylesheets decide where those values apply, so a deck palette cannot
accidentally override the portal body, navbar, or other page chrome.

The returned string is a complete `<style>`-able block; callers wrap it in
`<style>` themselves so the same producer can also be written to a `.css`
file when needed.
"""

from pygments.style import Style
from pygments.token import Comment, Keyword, Literal, Name, Operator, Punctuation, String, Text

from simplex.theme.tokens import WebPalette

_TOKEN_CSS_MAP: list[tuple[object, str]] = [
    (Text, "--simplex-code-text"),
    (Keyword, "--simplex-code-keyword"),
    (Name, "--simplex-code-name"),
    (Name.Function, "--simplex-code-function"),
    (Name.Class, "--simplex-code-class"),
    (Name.Builtin, "--simplex-code-builtin"),
    (Name.Decorator, "--simplex-code-decorator"),
    (Comment, "--simplex-code-comment"),
    (String, "--simplex-code-string"),
    (Literal.String, "--simplex-code-string"),
    (Literal.Number, "--simplex-code-number"),
    (Operator, "--simplex-code-operator"),
    (Punctuation, "--simplex-code-punctuation"),
]


def _extract_color(style_str: str) -> str | None:
    """Pull the first hex color from a Pygments style string like ``'bold #CC7832'``."""
    for part in style_str.split():
        if part.startswith("#") and len(part) in (4, 7, 9):
            return part
    return None


def render_code_style_css(style_cls: type[Style]) -> str:
    """Return CSS custom properties derived from a Pygments style class."""
    lines: list[str] = []
    bg = getattr(style_cls, "background_color", None)
    if bg:
        lines.append(f"  --simplex-code-bg: {bg};")
    style_map = getattr(style_cls, "styles", {})
    seen_vars: set[str] = set()
    for token, css_var in _TOKEN_CSS_MAP:
        if css_var in seen_vars:
            continue
        raw = style_map.get(token, "")
        color = _extract_color(raw)
        if color:
            lines.append(f"  {css_var}: {color};")
            seen_vars.add(css_var)
    return "\n".join(lines)


def render_web_css(palette: WebPalette, code_style: type[Style] | None = None) -> str:
    """Return a CSS variables block for `palette` and optionally a code style."""
    code_vars = ""
    if code_style is not None:
        code_vars = "\n" + render_code_style_css(code_style)
    return f""":root {{
  --simplex-accent: {palette.accent};
  --simplex-bg: {palette.background};
  --simplex-surface: {palette.surface};
  --simplex-text: {palette.text_primary};
  --simplex-text-muted: {palette.text_muted};
  --simplex-link: {palette.link};
  --simplex-code-bg: {palette.code_background};
  --simplex-font-sans: {palette.font_family_sans};
  --simplex-font-mono: {palette.font_family_mono};
  --simplex-font-size: {palette.font_size_base};{code_vars}
}}
"""
