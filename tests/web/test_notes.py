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
    assert 'class="language-python"' in html
    # Pygments wraps tokens in styled <span>s; check that the identifier and
    # literal made it through (each rendered as a colored span).
    assert ">x<" in html
    assert ">1<" in html


def test_fenced_code_block_uses_default_notes_keyword_color() -> None:
    html = render_text("```python\ndef f(): pass\n```\n")
    # Markdown notes default to SimplexSolarizedLight, independent of the
    # slide theme's code style. If the style ever drifts, this catches it.
    assert "#DB7448" in html.upper() or "#db7448" in html


def test_fenced_code_block_uses_default_notes_function_color() -> None:
    html = render_text("```python\ndef f(x):\n    return x\n```\n")
    html_upper = html.upper()

    assert "#06C" in html_upper or "#0066CC" in html_upper


def test_fenced_code_block_can_override_code_style() -> None:
    from simplex.theme.styles.simplex_pycharm import SimplexPycharm

    html = render_text("```python\ndef f(): pass\n```\n", code_style=SimplexPycharm)
    # SimplexPycharm renders Python keywords in #CC7832 -- if the style
    # ever drifts, this is where it'll show up first.
    assert "#CC7832" in html.upper() or "#cc7832" in html


def test_heading_emitted() -> None:
    html = render_text("# Section A\n\nbody\n")
    assert "<h1" in html
    assert "Section A" in html
