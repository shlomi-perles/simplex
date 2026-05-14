"""Markdown -> HTML with KaTeX-ready math and Pygments-friendly code blocks."""

from simplex.web.notes import render_text


def test_inline_math_marker() -> None:
    html = render_text("Energy is $E=mc^2$ for short.")
    assert 'class="math inline"' in html
    assert "E=mc^2" in html


def test_display_math_marker() -> None:
    html = render_text("Equation:\n\n$$\nE = mc^2\n$$\n")
    assert 'class="math block"' in html or 'class="math display"' in html
    assert "E = mc^2" in html


def test_fenced_code_block_survives() -> None:
    html = render_text("```python\nx = 1\n```\n")
    assert "<pre" in html
    assert "x = 1" in html


def test_heading_emitted() -> None:
    html = render_text("# Section A\n\nbody\n")
    assert "<h1" in html
    assert "Section A" in html
