"""Tufte-style sidenotes via ``^[note]`` inline footnote syntax."""

from simplex.web.notes import render_text


def test_inline_footnote_becomes_sidenote() -> None:
    html = render_text("Some text^[a marginal aside] continues.")
    # Tufte structure: inline ref + aside + no footnotes section.
    assert 'class="sidenote-ref"' in html
    assert 'class="sidenote"' in html
    assert "marginal aside" in html
    # The reference label sits between the body text and the aside.
    assert html.index('class="sidenote-ref"') < html.index('class="sidenote"')


def test_no_footnotes_section_at_bottom() -> None:
    html = render_text("Text^[sidenote] more.")
    assert 'class="footnotes"' not in html
    assert "footnote-backref" not in html


def test_multiple_sidenotes_get_unique_ids() -> None:
    html = render_text("One^[first] then two^[second].")
    assert 'id="sn-1"' in html
    assert 'id="sn-2"' in html
    assert html.count('class="sidenote"') == 2


def test_sidenote_keeps_inline_math() -> None:
    html = render_text("Energy^[the famous $E=mc^2$ identity] is conserved.")
    assert "E=mc^2" in html
    # Should be wrapped in KaTeX-friendly math markers, not raw `$`.
    assert "$E=mc^2$" not in html


def test_no_sidenote_when_no_footnotes() -> None:
    html = render_text("Plain text without any notes.")
    assert "sidenote" not in html


def test_slide_ref_inside_sidenote_does_not_hang() -> None:
    """Regression: silent-mode inline rules must advance `state.pos`, otherwise
    `parseLinkLabel` (called by footnote_plugin) loops forever when scanning
    a `^[...]` body that contains a `[slide:N]` bracket pair."""
    html = render_text("Body^[see [slide:2] for details].", slide_count=8)
    assert 'class="sidenote"' in html
    assert 'class="slide-ref"' in html


def test_cite_inside_sidenote_does_not_hang() -> None:
    """Same regression for `\\cite{...}` inside `^[...]`."""
    from simplex.web.bibliography import Bibliography

    bib = Bibliography.parse("@article{x, author = {Smith, J.}, title = {T}, year = 2020}")
    html = render_text(r"Body^[refer to \cite{x}].", bibliography=bib)
    assert 'class="sidenote"' in html
    assert 'class="cite"' in html
