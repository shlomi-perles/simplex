"""Render a `WebPalette` to a `:root { --simplex-* }` CSS variables block.

Consumed by two surfaces:
- the portal `<head>` (homepage cards + section pages)
- per-deck RevealJS HTML `<head>` (slide chrome, captions)

The returned string is a complete `<style>`-able block; callers wrap it in
`<style>` themselves so the same producer can also be written to a `.css`
file when needed.
"""

from simplex.theme.tokens import WebPalette


def render_web_css(palette: WebPalette) -> str:
    """Return a CSS variables block for `palette` plus a few default rules."""
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
  --simplex-font-size: {palette.font_size_base};
}}

body {{
  background: var(--simplex-bg);
  color: var(--simplex-text);
  font-family: var(--simplex-font-sans);
  font-size: var(--simplex-font-size);
}}

a {{
  color: var(--simplex-link);
}}

code, pre, .hljs {{
  background: var(--simplex-code-bg);
  font-family: var(--simplex-font-mono);
}}

.reveal {{
  background: var(--simplex-bg);
  color: var(--simplex-text);
}}

.reveal .progress {{
  color: var(--simplex-accent);
}}
"""
