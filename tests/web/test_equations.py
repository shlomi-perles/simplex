r"""Display-math `\tag{X}` extraction + `\ref{eq-X}` resolution."""

from simplex.web import equations
from simplex.web.notes import render_text


def test_tag_extracted_and_id_assigned() -> None:
    html, labels = equations.transform('<div class="math block">\n\\[E = mc^2 \\tag{1}\\]\n</div>')
    assert 'id="eq-1"' in html
    assert 'class="eq-tag">(1)</span>' in html
    # The \tag macro is removed from the math content so KaTeX doesn't
    # render its own (overlapping) tag.
    assert "\\tag" not in html
    assert labels == {"eq-1": "(1)"}


def test_tag_with_word_label_slugified() -> None:
    html, labels = equations.transform('<div class="math block">\n\\[x=y \\tag{AdaGrad}\\]\n</div>')
    assert 'id="eq-adagrad"' in html
    assert labels == {"eq-adagrad": "(AdaGrad)"}


def test_block_without_tag_left_alone() -> None:
    raw = '<div class="math block">\n\\[E = mc^2\\]\n</div>'
    html, labels = equations.transform(raw)
    assert html == raw
    assert labels == {}


def test_duplicate_slugs_get_unique_suffix() -> None:
    raw = (
        '<div class="math block">\\[a \\tag{3}\\]</div>\n'
        '<div class="math block">\\[b \\tag{3}\\]</div>'
    )
    html, labels = equations.transform(raw)
    assert 'id="eq-3"' in html
    assert 'id="eq-3-2"' in html
    assert set(labels) == {"eq-3", "eq-3-2"}


def test_ref_resolves_equation_label_through_notes_pipeline() -> None:
    """End-to-end: an inline \\ref{} pointing at an equation tag should
    be rewritten to the linked display label."""
    md = (
        "$$\nx_{t+1} = x_t - \\eta \\nabla f(x_t) \\tag{3}\n$$\n\n"
        r"See \ref{eq-3} for the bound."
    )
    html = render_text(md)
    assert 'class="ref"' in html
    assert 'href="#eq-3"' in html
    assert ">(3)<" in html
    # The label-stripped math no longer carries the LaTeX \tag macro.
    assert "\\tag" not in html


def test_ref_to_missing_equation_is_stale() -> None:
    html = render_text(r"See \ref{eq-missing}.")
    assert "ref-stale" in html


def test_equation_with_tag_and_callout_coexist() -> None:
    md = (
        "$$\\Sigma = 0 \\tag{C1}$$\n\n"
        "> **Theorem 1.** body referring to \\ref{eq-c1} and \\ref{theorem-1}.\n"
    )
    html = render_text(md)
    # Equation labelled and theorem labelled.
    assert 'id="eq-c1"' in html
    assert 'id="theorem-1"' in html
    # Both refs resolve.
    assert 'href="#eq-c1"' in html
    assert 'href="#theorem-1"' in html
    assert ">(C1)<" in html
    assert ">Theorem 1<" in html
