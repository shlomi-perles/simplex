r"""Theorem-environment callouts + `\ref{}` resolution."""

from simplex.web.notes import render_text


def test_theorem_blockquote_becomes_callout() -> None:
    html = render_text("> **Theorem 3.1.** Let $f$ be convex.\n")
    assert 'class="callout callout-theorem"' in html
    assert 'id="theorem-3-1"' in html
    assert "<blockquote>" not in html
    # The `<strong>` tag rewrites to the callout tag span.
    assert 'class="callout-tag"' in html
    assert ">Theorem 3.1.<" in html


def test_definition_uses_amber_palette_via_class() -> None:
    """Class hook only; the actual colour lives in `simplex.css`."""
    html = render_text("> **Definition.** A graph is...\n")
    assert "callout-definition" in html
    # Unnumbered callouts auto-number sequentially.
    assert 'id="definition-1"' in html


def test_lemma_proposition_corollary_remark() -> None:
    for tag, klass in [
        ("Lemma 4.2", "callout-lemma"),
        ("Proposition 2", "callout-proposition"),
        ("Corollary 5.7", "callout-corollary"),
        ("Remark", "callout-remark"),
        ("Example 1.1", "callout-example"),
        ("Proof", "callout-proof"),
    ]:
        html = render_text(f"> **{tag}.** body\n")
        assert klass in html, f"missing {klass} for {tag!r}"


def test_blockquote_without_tag_is_untouched() -> None:
    html = render_text("> Just a quote.\n")
    assert "<blockquote>" in html
    assert "callout" not in html


def test_blockquote_with_tag_not_at_top_is_untouched() -> None:
    """`**Theorem 3.1.**` mid-paragraph is a textual reference, not a tag."""
    html = render_text("> Some prelude. **Theorem 3.1.** later.\n")
    assert "<blockquote>" in html
    assert "callout-theorem" not in html


def test_ref_resolves_to_display_label() -> None:
    md = (
        "> **Theorem 3.1.** Let $f$ be convex.\n\n"
        r"See \ref{theorem-3-1} for the bound."
    )
    html = render_text(md)
    assert 'class="ref"' in html
    assert 'href="#theorem-3-1"' in html
    # Resolved to the display label, not the raw id.
    assert ">Theorem 3.1<" in html
    assert ">theorem-3-1<" not in html


def test_unresolved_ref_marked_stale() -> None:
    html = render_text(r"See \ref{theorem-9-9}.")
    assert "ref-stale" in html
    assert "?" in html  # the fallback suffix


def test_unnumbered_callouts_get_unique_ids() -> None:
    md = "> **Proof.** First proof.\n\nintermezzo\n\n> **Proof.** Second proof.\n"
    html = render_text(md)
    assert 'id="proof-1"' in html
    assert 'id="proof-2"' in html


def test_callout_inside_blockquote_keeps_inner_strong() -> None:
    """A theorem with an inline `**Proof.**` paragraph keeps the proof
    label in the body (we only re-tag the outer callout)."""
    md = "> **Theorem 1.** Claim.\n>\n> **Proof.** Argument."
    html = render_text(md)
    assert "callout-theorem" in html
    # The inline Proof. stays as bold (no nested aside).
    assert html.count("<aside") == 1
    assert "<strong>Proof.</strong>" in html


def test_ref_inside_sidenote() -> None:
    """`\\ref{}` should work inside `^[...]` -- mirrors the slide_ref /
    \\cite{} regression."""
    md = "> **Theorem 1.** body\n\nbody^[as in \\ref{theorem-1}] more"
    html = render_text(md)
    assert 'class="ref"' in html
    assert 'class="sidenote"' in html


def test_callout_preserves_math_inside() -> None:
    """KaTeX delimiters survive callout rewriting."""
    md = "> **Theorem 1.** $E=mc^2$ is famous."
    html = render_text(md)
    assert "callout-theorem" in html
    # dollarmath should have turned `$E=mc^2$` into a katex-friendly span.
    assert "math inline" in html
    assert "E=mc^2" in html
