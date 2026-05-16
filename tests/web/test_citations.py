r"""`\cite{key}` markdown plugin -> alpha tags + bibliography section."""

from simplex.web.bibliography import Bibliography
from simplex.web.notes import render_text


def _bib() -> Bibliography:
    return Bibliography.parse(
        """
        @article{DHS11,
          author = {Duchi, J. and Hazan, E. and Singer, Y.},
          title = {Adaptive subgradient methods},
          journal = {JMLR}, year = 2011,
        }
        @inproceedings{KB15,
          author = {Kingma, D. P. and Ba, J.},
          title = {Adam: A Method for Stochastic Optimization},
          booktitle = {ICLR}, year = 2015,
        }
        """
    )


def test_cite_emits_alpha_anchor() -> None:
    html = render_text(r"See \cite{KB15} for ADAM.", bibliography=_bib())
    assert 'class="cite"' in html
    assert 'href="#bib-KB15"' in html
    assert ">KB15<" in html


def test_multi_key_cite_emits_one_group() -> None:
    html = render_text(r"Both \cite{DHS11, KB15} matter.", bibliography=_bib())
    assert html.count('class="cite-group"') == 1
    assert ">DHS11<" in html
    assert ">KB15<" in html


def test_unknown_key_marked_stale() -> None:
    html = render_text(r"Bogus \cite{NotReal} here.", bibliography=_bib())
    assert "cite-stale" in html


def test_bibliography_section_appended_when_cited() -> None:
    html = render_text(r"Use \cite{KB15}.", bibliography=_bib())
    assert 'class="bibliography"' in html
    assert 'id="bib-KB15"' in html
    # The uncited DHS11 entry stays out of the rendered list.
    assert "Duchi" not in html


def test_bibliography_section_omitted_when_no_citations() -> None:
    html = render_text("Plain text.", bibliography=_bib())
    assert '<section class="bibliography"' not in html


def test_no_bib_renders_stale_marker() -> None:
    """Notes that cite without a bib argument fall back to stale chips."""
    html = render_text(r"See \cite{KB15}.", bibliography=None)
    assert "cite-stale" in html


def test_cite_inside_paragraph_inline() -> None:
    """The plugin must not break the surrounding paragraph."""
    html = render_text(r"Text before \cite{KB15} and after.", bibliography=_bib())
    assert "<p>" in html
    assert html.count("<p>") == 1


def test_cite_with_bracket_in_other_text_unaffected() -> None:
    """Square-bracket text that isn't \\cite{...} must pass through."""
    html = render_text("Note [not a cite] verbatim.", bibliography=_bib())
    assert "[not a cite]" in html
