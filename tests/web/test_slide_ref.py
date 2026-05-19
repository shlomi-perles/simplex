"""[slide:N] markdown plugin: emits anchors and flags out-of-range refs."""

from simplex.web.notes import render_text


def test_slide_ref_emits_anchor() -> None:
    html = render_text("See [slide:3] for details.", slide_count=10)
    assert 'class="slide-ref"' in html
    # 1-based to match the sidebar's data-slide-target convention.
    assert 'data-slide="3"' in html
    assert ">3</a>" in html


def test_slide_ref_out_of_range_flagged() -> None:
    html = render_text("Bad: [slide:99].", slide_count=2)
    assert "slide-ref-stale" in html


def test_slide_ref_without_count_renders_anchor() -> None:
    html = render_text("Open [slide:1].", slide_count=None)
    assert 'class="slide-ref"' in html
    assert "slide-ref-stale" not in html


def test_non_slide_brackets_passthrough() -> None:
    html = render_text("[link](http://x) and [text]", slide_count=10)
    assert 'href="http://x"' in html
