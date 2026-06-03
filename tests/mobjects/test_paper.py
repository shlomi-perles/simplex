"""Tests for the Paper mobject and its animations."""

from pathlib import Path

import pytest

pytest.importorskip("manim")

import manim
import numpy as np
from manim import DL, DOWN, RIGHT, UP, ImageMobject, config

from simplex.engine.defaults import apply_theme_defaults
from simplex.mobjects.paper import (
    DismissPaper,
    Paper,
    PickPage,
    ShowPaper,
    _render_pages,
    _url_to_pdf_url,
)
from simplex.theme.presets import SIMPLEX_DARK, SIMPLEX_LIGHT


@pytest.fixture
def sample_pdf(tmp_path: Path) -> Path:
    """Create a minimal multi-page PDF for testing."""
    import ctypes

    import pypdfium2 as pdfium
    import pypdfium2.raw as pdfium_c

    pdf_path = tmp_path / "test.pdf"
    doc = pdfium.PdfDocument.new()
    font = pdfium.PdfFont.load_standard(doc, "Helvetica")
    for i in range(5):
        page = doc.new_page(612, 792)
        text = f"Page {i + 1}"
        raw_obj = pdfium_c.FPDFPageObj_CreateTextObj(doc.raw, font.raw, 24.0)
        encoded = (text + "\x00").encode("utf-16-le")
        buf = ctypes.create_string_buffer(encoded)
        pdfium_c.FPDFText_SetText(raw_obj, ctypes.cast(buf, ctypes.POINTER(ctypes.c_ushort)))
        pdfium_c.FPDFPageObj_Transform(raw_obj, 1, 0, 0, 1, 72, 720)
        pdfium_c.FPDFPage_InsertObject(page.raw, raw_obj)
        pdfium_c.FPDFPage_GenerateContent(page.raw)
    with pdf_path.open("wb") as f:
        doc.save(f)
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


def test_paper_default_has_shadow_without_border(sample_pdf: Path) -> None:
    paper = Paper(sample_pdf, pages=1, dpi=72, page_height=4.0)
    assert len(paper.get_top_page().submobjects) == 2


def test_paper_default_stack_offset_is_small(sample_pdf: Path) -> None:
    paper = Paper(sample_pdf, pages=2, dpi=72, page_height=4.0, shadow=False)
    assert np.allclose(paper.get_page(1).get_center(), DL * 0.2, atol=0.01)


def test_paper_top_page_at_origin(sample_pdf: Path) -> None:
    paper = Paper(sample_pdf, pages=3, dpi=72, page_height=4.0)
    assert np.allclose(paper.get_top_page().get_center(), [0, 0, 0], atol=0.01)


def test_paper_pages_have_front_to_back_z_indices(sample_pdf: Path) -> None:
    paper = Paper(sample_pdf, pages=3, dpi=72, page_height=4.0)
    z_indices = [pg.z_index for pg in paper.page_groups]
    assert z_indices == sorted(z_indices, reverse=True)


def test_paper_reorder_to_top(sample_pdf: Path) -> None:
    paper = Paper(sample_pdf, pages=3, dpi=72, page_height=4.0)
    original_back = paper.get_page(2)
    paper.reorder_page_to_top(2)
    assert paper.get_top_page() is original_back


def test_paper_reorder_preserves_transformed_stack_layout(sample_pdf: Path) -> None:
    paper = Paper(sample_pdf, pages=3, dpi=72, page_height=4.0, shadow=False)
    paper.scale(0.5)
    paper.shift(2 * RIGHT + UP)
    anchor = paper.get_top_page().get_center().copy()
    step = paper.get_page(1).get_center() - paper.get_top_page().get_center()
    original_back = paper.get_page(2)

    paper.reorder_page_to_top(2)

    assert paper.get_top_page() is original_back
    for i, page in enumerate(paper.page_groups):
        assert np.allclose(page.get_center(), anchor + step * i, atol=0.01)


def test_show_paper_constructs(sample_pdf: Path) -> None:
    paper = Paper(sample_pdf, pages=2, dpi=72, page_height=3.0)
    anim = ShowPaper(paper, direction=DOWN)
    assert anim.run_time == 1.5


def test_dismiss_paper_constructs(sample_pdf: Path) -> None:
    paper = Paper(sample_pdf, pages=2, dpi=72, page_height=3.0)
    anim = DismissPaper(paper, direction=UP)
    assert anim.run_time == 1.5


def test_pick_page_constructs(sample_pdf: Path) -> None:
    paper = Paper(sample_pdf, pages=3, dpi=72, page_height=3.0)
    anim = PickPage(paper, page_index=2, slide_direction=RIGHT)
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


def test_paper_default_border_uses_active_manim_white(sample_pdf: Path) -> None:
    try:
        apply_theme_defaults(SIMPLEX_LIGHT)
        paper = Paper(sample_pdf, pages=1, dpi=72, page_height=3.0, shadow=False, border=True)
        border = paper.get_top_page().submobjects[-1]
        assert border.get_stroke_color().to_hex() == manim.WHITE.to_hex()
    finally:
        apply_theme_defaults(SIMPLEX_DARK)


def test_paper_with_shadow_and_border(sample_pdf: Path) -> None:
    paper = Paper(sample_pdf, pages=2, dpi=72, page_height=3.0, shadow=True, border=True)
    for pg in paper.page_groups:
        assert len(pg.submobjects) == 3


def test_paper_shadow_is_blurred_image(sample_pdf: Path) -> None:
    paper = Paper(sample_pdf, pages=1, dpi=72, page_height=3.0, shadow=True, border=False)
    shadow = paper.get_top_page().submobjects[0]
    page_image = paper.get_top_page().submobjects[1]

    assert isinstance(shadow, ImageMobject)
    assert shadow.width > page_image.width
    assert shadow.height > page_image.height
    assert shadow.width < config.frame_width * 0.5
    assert shadow.height < config.frame_height * 0.7


def test_pick_page_preserves_z_index_until_slide_out(sample_pdf: Path) -> None:
    paper = Paper(sample_pdf, pages=3, dpi=72, page_height=3.0)
    selected = paper.get_page(1)
    original_selected_z = selected.z_index
    original_z_indices = [pg.z_index for pg in paper.page_groups]
    anim = PickPage(paper, page_index=1, slide_direction=RIGHT)

    anim.begin()
    assert selected.z_index == original_selected_z
    assert [pg.z_index for pg in paper.page_groups] == original_z_indices

    anim.interpolate_mobject(0.49)
    assert selected.z_index == original_selected_z

    anim.interpolate_mobject(0.5)
    assert paper.get_top_page() is selected
    other_z = [pg.z_index for pg in paper.page_groups if pg is not selected]
    assert selected.z_index > max(other_z)
    anim.finish()


def test_pick_page_preserves_transformed_stack_layout(sample_pdf: Path) -> None:
    paper = Paper(sample_pdf, pages=3, dpi=72, page_height=4.0, shadow=False)
    paper.scale(0.5)
    paper.shift(2 * RIGHT + UP)
    anchor = paper.get_top_page().get_center().copy()
    step = paper.get_page(1).get_center() - paper.get_top_page().get_center()
    selected = paper.get_page(2)
    anim = PickPage(paper, page_index=2, slide_direction=RIGHT)

    anim.begin()
    anim.interpolate_mobject(1.0)
    anim.finish()

    assert paper.get_top_page() is selected
    for i, page in enumerate(paper.page_groups):
        assert np.allclose(page.get_center(), anchor + step * i, atol=0.01)


def test_dismiss_is_show_subclass(sample_pdf: Path) -> None:
    paper = Paper(sample_pdf, pages=2, dpi=72, page_height=3.0)
    anim = DismissPaper(paper, direction=UP)
    assert isinstance(anim, ShowPaper)
