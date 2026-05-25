"""Tests for the Paper mobject and its animations."""

from pathlib import Path

import pytest

pytest.importorskip("manim")

import numpy as np

from simplex.mobjects.paper import (
    DismissPaper,
    Paper,
    PickPage,
    ShowPaper,
    _render_pages,
    _url_to_pdf_url,
)


@pytest.fixture
def sample_pdf(tmp_path: Path) -> Path:
    """Create a minimal multi-page PDF for testing."""
    import pymupdf

    pdf_path = tmp_path / "test.pdf"
    doc = pymupdf.open()
    for i in range(5):
        page = doc.new_page(width=612, height=792)
        tw = pymupdf.TextWriter(page.rect)
        tw.append((72, 72), f"Page {i + 1}", fontsize=24)
        tw.write_text(page)
    doc.save(pdf_path)
    doc.close()
    return pdf_path


def test_arxiv_url_normalization() -> None:
    assert _url_to_pdf_url("https://arxiv.org/abs/1706.03762") == (
        "https://arxiv.org/pdf/1706.03762.pdf"
    )
    assert _url_to_pdf_url("https://arxiv.org/pdf/1706.03762") == (
        "https://arxiv.org/pdf/1706.03762.pdf"
    )
    assert _url_to_pdf_url("https://arxiv.org/pdf/1706.03762.pdf") == (
        "https://arxiv.org/pdf/1706.03762.pdf"
    )


def test_render_pages_creates_images(sample_pdf: Path) -> None:
    pages = _render_pages(sample_pdf, pages=3, dpi=72)
    assert len(pages) == 3
    for p in pages:
        assert p.exists()
        assert p.suffix == ".png"


def test_render_pages_clamps_to_document_length(sample_pdf: Path) -> None:
    pages = _render_pages(sample_pdf, pages=100, dpi=72)
    assert len(pages) == 5


def test_paper_constructs_with_local_pdf(sample_pdf: Path) -> None:
    paper = Paper(sample_pdf, pages=3, dpi=72, page_height=4.0)
    assert paper.page_count == 3
    assert len(paper.submobjects) == 3


def test_paper_top_page_at_origin(sample_pdf: Path) -> None:
    paper = Paper(sample_pdf, pages=3, dpi=72, page_height=4.0)
    assert np.allclose(paper.get_top_page().get_center(), [0, 0, 0], atol=0.01)


def test_paper_reorder_to_top(sample_pdf: Path) -> None:
    paper = Paper(sample_pdf, pages=3, dpi=72, page_height=4.0)
    original_back = paper.get_page(2)
    paper.reorder_page_to_top(2)
    assert paper.get_top_page() is original_back


def test_show_paper_constructs(sample_pdf: Path) -> None:
    paper = Paper(sample_pdf, pages=2, dpi=72, page_height=3.0)
    anim = ShowPaper(paper, direction="DOWN")
    assert anim.run_time == 1.5


def test_dismiss_paper_constructs(sample_pdf: Path) -> None:
    paper = Paper(sample_pdf, pages=2, dpi=72, page_height=3.0)
    anim = DismissPaper(paper, direction="UP")
    assert anim.run_time == 1.5


def test_pick_page_constructs(sample_pdf: Path) -> None:
    paper = Paper(sample_pdf, pages=3, dpi=72, page_height=3.0)
    anim = PickPage(paper, page_index=2, slide_direction="RIGHT")
    assert anim.run_time == 2.0


def test_pick_page_out_of_range_raises(sample_pdf: Path) -> None:
    paper = Paper(sample_pdf, pages=3, dpi=72, page_height=3.0)
    with pytest.raises(IndexError):
        PickPage(paper, page_index=5)


def test_paper_exit_animation_is_dismiss(sample_pdf: Path) -> None:
    from simplex.engine.animations import exit_for

    paper = Paper(sample_pdf, pages=2, dpi=72, page_height=3.0)
    anim = exit_for(paper)
    assert isinstance(anim, DismissPaper)


def test_paper_without_shadow(sample_pdf: Path) -> None:
    paper = Paper(sample_pdf, pages=2, dpi=72, page_height=3.0, shadow=False, border=False)
    assert paper.page_count == 2
    for pg in paper.page_groups:
        assert len(pg.submobjects) == 1


def test_paper_with_border_no_shadow(sample_pdf: Path) -> None:
    paper = Paper(sample_pdf, pages=2, dpi=72, page_height=3.0, shadow=False, border=True)
    assert paper.page_count == 2
    for pg in paper.page_groups:
        assert len(pg.submobjects) == 2


def test_paper_with_shadow_and_border(sample_pdf: Path) -> None:
    paper = Paper(sample_pdf, pages=2, dpi=72, page_height=3.0, shadow=True, border=True)
    for pg in paper.page_groups:
        assert len(pg.submobjects) == 3


def test_dismiss_is_show_subclass(sample_pdf: Path) -> None:
    paper = Paper(sample_pdf, pages=2, dpi=72, page_height=3.0)
    anim = DismissPaper(paper, direction="UP")
    assert isinstance(anim, ShowPaper)
