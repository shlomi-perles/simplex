"""Paper mobject -- render academic papers (ArXiv / local PDF / BibTeX) as stacked page images.

Provides:
- ``Paper``: a ``Group`` of ``ImageMobject`` pages with configurable shadow and stacking.
- ``ShowPaper``: intro animation that builds the stacked view.
- ``DismissPaper``: exit animation — delegates to ``ShowPaper`` with reversed fade direction.
- ``PickPage``: pull-from-stack animation for a given page index.
"""

from __future__ import annotations

import logging
import re
import urllib.request
from collections.abc import Sequence
from pathlib import Path
from typing import Any, Self, cast

import numpy as np
import pypdfium2 as pdfium
from manim import (
    DL,
    DOWN,
    RIGHT,
    WHITE,
    Animation,
    AnimationGroup,
    FadeIn,
    FadeOut,
    Group,
    ImageMobject,
    Rectangle,
    RoundedRectangle,
    Scene,
    config,
    smooth,
)
from manim.camera.camera import Camera
from manim.mobject.opengl.opengl_compatibility import ConvertToOpenGL
from manim.utils.color import ParsableManimColor
from manim.utils.tex_file_writing import tex_hash
from PIL import ImageFilter

from simplex.engine.opengl_compat import MobjectLike

logger = logging.getLogger("simplex.paper")

_DEFAULT_DPI = 150
_DEFAULT_PAGES = 3
_DEFAULT_TIMEOUT = 30
_SHADOW_OPACITY = 0.22
_SHADOW_COLOR = "#000000"
_SHADOW_OFFSET_FACTOR = 0.025
_SHADOW_BLUR = 12.0
_SHADOW_SCALE = 1.04
_STACK_OFFSET_FACTOR = 0.08
_PAGE_HEIGHT = 5.5
_BORDER_COLOR = WHITE
_BORDER_STROKE_WIDTH = 1.5

_ARXIV_ABS_RE = re.compile(r"arxiv\.org/abs/(.+?)(?:\?|$)")
_ARXIV_PDF_RE = re.compile(r"arxiv\.org/pdf/(.+?)(?:\.pdf)?(?:\?|$)")


def _paper_dir() -> Path:
    """Return (and create) the paper cache directory inside Manim's media tree."""
    d = Path(config.media_dir) / "papers"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _url_to_pdf_url(url: str) -> str:
    """Normalize an ArXiv URL to a direct PDF download link."""
    if m := _ARXIV_ABS_RE.search(url):
        return f"https://arxiv.org/pdf/{m.group(1)}.pdf"
    if _ARXIV_PDF_RE.search(url):
        return url if url.endswith(".pdf") else url + ".pdf"
    return url


def _download_pdf(url: str, *, timeout: int = _DEFAULT_TIMEOUT) -> Path:
    """Download a PDF from *url*, caching on disk. Returns local path."""
    key = tex_hash(url)
    cached = _paper_dir() / f"{key}.pdf"
    if cached.exists():
        return cached
    pdf_url = _url_to_pdf_url(url)
    if not pdf_url.startswith(("https://", "http://")):
        raise ValueError(f"Refusing to open non-HTTP URL: {pdf_url}")
    logger.info("Downloading %s → %s", pdf_url, cached)
    req = urllib.request.Request(pdf_url, headers={"User-Agent": "manim-simplex/0.2"})  # noqa: S310
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310
        cached.write_bytes(resp.read())
    return cached


def _resolve_bibtex_source(bib_path: Path, cite_key: str) -> str:
    """Extract an ArXiv URL or ``eprint`` field from a BibTeX entry."""
    text = bib_path.read_text()
    pattern = re.compile(
        rf"@\w+\{{\s*{re.escape(cite_key)}\s*,(.*?)\n\s*\}}",
        re.DOTALL,
    )
    match = pattern.search(text)
    if not match:
        raise ValueError(f"Cite key '{cite_key}' not found in {bib_path}")
    body = match.group(1)
    if ep := re.search(r"eprint\s*=\s*\{?([0-9.]+)\}?", body):
        return f"https://arxiv.org/abs/{ep.group(1)}"
    if url_match := re.search(r"url\s*=\s*\{(.+?)\}", body):
        return url_match.group(1)
    raise ValueError(f"No ArXiv eprint or URL found for '{cite_key}' in {bib_path}")


def _render_pages(
    pdf_path: Path,
    *,
    pages: int = _DEFAULT_PAGES,
    dpi: int = _DEFAULT_DPI,
) -> list[Path]:
    """Render the first *pages* pages of a PDF to cached PNGs."""
    key = tex_hash(str(pdf_path))
    cache = _paper_dir() / key
    cache.mkdir(parents=True, exist_ok=True)

    rendered: list[Path] = []
    doc = pdfium.PdfDocument(pdf_path)
    n = min(pages, len(doc))
    scale = dpi / 72.0
    for i in range(n):
        out = cache / f"page_{i}_dpi{dpi}.png"
        if not out.exists():
            bitmap = doc[i].render(scale=scale)
            bitmap.to_pil().save(out)
            logger.info("Rendered %s page %d → %s", pdf_path.name, i, out)
        rendered.append(out)
    doc.close()
    return rendered


def _blurred_mobject_image(
    mobjects: Sequence[MobjectLike],
    *,
    blur_radius: float,
    scale_first: float,
) -> ImageMobject:
    """Rasterize mobjects into a tightly cropped, blurred ``ImageMobject``."""
    scene = Scene()
    renderer = scene.renderer
    camera = cast(Camera, renderer.camera)

    copies = Group(
        *[mob.copy().scale(scale_first, about_point=mob.get_center()) for mob in mobjects]
    )
    camera.set_pixel_array(np.zeros_like(camera.pixel_array))
    camera.capture_mobjects(copies)

    image = camera.get_image().convert("RGBA").filter(ImageFilter.GaussianBlur(blur_radius))
    bbox = image.getchannel("A").getbbox()
    if bbox is None:
        return ImageMobject(np.array(image))

    cropped = image.crop(bbox)
    pixel_width = image.width
    pixel_height = image.height
    frame_width = float(config.frame_width)
    frame_height = float(config.frame_height)

    left, top, right, bottom = bbox
    center_x = ((left + right) / 2 / pixel_width - 0.5) * frame_width
    center_y = (0.5 - (top + bottom) / 2 / pixel_height) * frame_height
    width = (right - left) / pixel_width * frame_width

    return (
        ImageMobject(np.array(cropped)).scale_to_fit_width(width).move_to((center_x, center_y, 0.0))
    )


# ---------------------------------------------------------------------------
# Paper mobject
# ---------------------------------------------------------------------------


class Paper(Group, metaclass=ConvertToOpenGL):
    """A stack of rendered PDF pages displayed as ``ImageMobject`` instances.

    Parameters
    ----------
    source
        One of: ArXiv URL, local PDF path, or ``(bib_path, cite_key)`` tuple.
    pages
        Number of pages to render (from the start of the document).
    dpi
        Resolution for PDF-to-image conversion.
    page_height
        Target height of each page in Manim units.
    shadow
        Whether to render a drop shadow behind pages.
    shadow_direction
        Direction the shadow falls (Manim direction vector, e.g. ``DL``).
    shadow_opacity
        Opacity of the shadow silhouette before it is blurred.
    shadow_blur
        Gaussian blur radius in rendered pixels.
    shadow_scale
        Scale applied to the shadow silhouette before rasterization.
    border
        Whether to draw a thin border around each page.
    border_color
        Stroke color for the page border.
    border_stroke_width
        Stroke width for the page border.
    stack_direction
        Direction pages stack towards (Manim direction vector, e.g. ``DL``).
    stack_offset
        Distance between consecutive pages in the stack (Manim units).
    timeout
        Network timeout in seconds for downloading.
    """

    def __init__(
        self,
        source: str | Path | tuple[Path | str, str],
        *,
        pages: int = _DEFAULT_PAGES,
        dpi: int = _DEFAULT_DPI,
        page_height: float = _PAGE_HEIGHT,
        shadow: bool = True,
        shadow_direction: np.ndarray = DL,
        shadow_opacity: float = _SHADOW_OPACITY,
        shadow_blur: float = _SHADOW_BLUR,
        shadow_scale: float = _SHADOW_SCALE,
        border: bool = True,
        border_color: ParsableManimColor = _BORDER_COLOR,
        border_stroke_width: float = _BORDER_STROKE_WIDTH,
        stack_direction: np.ndarray = DL,
        stack_offset: float | None = None,
        timeout: int = _DEFAULT_TIMEOUT,
        **kwargs: Any,
    ) -> None:
        self._shadow_enabled = shadow

        pdf_path = self._resolve_source(source, timeout=timeout)
        image_paths = _render_pages(pdf_path, pages=pages, dpi=dpi)

        shadow_dir = np.asarray(shadow_direction, dtype=float)
        self._stack_dir = np.asarray(stack_direction, dtype=float)
        self._stack_offset = (
            stack_offset if stack_offset is not None else page_height * _STACK_OFFSET_FACTOR
        )

        page_groups: list[Group] = []
        for img_path in image_paths:
            img = ImageMobject(str(img_path))
            img.height = page_height

            parts: list[Any] = []

            if shadow:
                shadow_shape = RoundedRectangle(
                    width=img.width,
                    height=img.height,
                    corner_radius=0.04,
                    fill_color=_SHADOW_COLOR,
                    fill_opacity=shadow_opacity,
                    stroke_width=0,
                )
                shadow_offset = shadow_dir * page_height * _SHADOW_OFFSET_FACTOR
                shadow_shape.move_to(img.get_center() + shadow_offset)
                parts.append(
                    _blurred_mobject_image(
                        [shadow_shape],
                        blur_radius=shadow_blur,
                        scale_first=shadow_scale,
                    )
                )

            parts.append(img)

            if border:
                border_rect = Rectangle(
                    width=img.width,
                    height=img.height,
                    stroke_color=border_color,
                    stroke_width=border_stroke_width,
                    stroke_opacity=0.6,
                    fill_opacity=0,
                )
                border_rect.move_to(img.get_center())
                parts.append(border_rect)

            page_groups.append(Group(*parts))

        # _page_groups[0] = top/front page (first PDF page), drawn last.
        # Submobjects stored back-to-front for correct z-order.
        self._page_groups = page_groups
        super().__init__(*reversed(page_groups), **kwargs)
        self._arrange_stack()
        self._sync_submobjects()

    # -- source resolution ---------------------------------------------------

    def _resolve_source(self, source: str | Path | tuple[Path | str, str], *, timeout: int) -> Path:
        if isinstance(source, tuple):
            bib_path, cite_key = source
            url = _resolve_bibtex_source(Path(bib_path), cite_key)
            return _download_pdf(url, timeout=timeout)
        source_str = str(source)
        if source_str.startswith(("http://", "https://")):
            return _download_pdf(source_str, timeout=timeout)
        path = Path(source_str)
        if not path.exists():
            raise FileNotFoundError(f"PDF not found: {path}")
        return path

    # -- layout --------------------------------------------------------------

    def _arrange_stack(self) -> None:
        """Position pages: page 0 at origin (top), others offset behind."""
        for i, pg in enumerate(self._page_groups):
            pg.move_to(self._stack_dir * self._stack_offset * i)

    def _sync_submobjects(self) -> None:
        """Keep submobject draw order and z-index in front-page order."""
        self.submobjects = list(reversed(self._page_groups))
        self._sync_page_z_indices()

    def _sync_page_z_indices(self) -> None:
        base_z = self.z_index
        count = len(self._page_groups)
        for front_index, pg in enumerate(self._page_groups):
            pg.set_z_index(base_z + count - front_index, family=True)

    def _set_page_order(self, page_groups: list[Group], *, arrange: bool) -> None:
        self._page_groups = list(page_groups)
        self._sync_submobjects()
        if arrange:
            self._arrange_stack()

    # -- public API ----------------------------------------------------------

    @property
    def page_groups(self) -> list[Group]:
        return list(self._page_groups)

    @property
    def page_count(self) -> int:
        return len(self._page_groups)

    def get_page(self, index: int) -> Group:
        return self._page_groups[index]

    def get_top_page(self) -> Group:
        return self._page_groups[0]

    def reorder_page_to_top(self, index: int) -> None:
        """Move page at *index* to position 0 (front of stack, drawn last)."""
        pages = list(self._page_groups)
        page = pages.pop(index)
        pages.insert(0, page)
        self._set_page_order(pages, arrange=True)


# ---------------------------------------------------------------------------
# Animations
# ---------------------------------------------------------------------------


class ShowPaper(AnimationGroup):
    """Intro animation: pages cascade in with a lagged stagger.

    Back pages appear first, then the front page lands on top — giving a
    natural "dealing cards" effect.

    When *dismiss* is ``True`` the animation flips to ``FadeOut`` and the
    cascade order reverses (front page exits first), so ``DismissPaper``
    can delegate here without duplicating the logic.

    Parameters
    ----------
    paper
        The Paper mobject to animate.
    direction
        Direction from which pages slide in (intro) or out (dismiss). Pass a
        Manim direction vector such as ``DOWN`` or ``UP``.
    lag_ratio
        Stagger between successive page animations.
    dismiss
        If ``True``, use ``FadeOut`` (exit) instead of ``FadeIn`` (intro).
    """

    def __new__(
        cls,
        paper: Paper,
        *,
        direction: np.ndarray = DOWN,
        lag_ratio: float = 0.3,
        dismiss: bool = False,
        use_override: bool = True,
        **kwargs: Any,
    ) -> Self:
        return super().__new__(
            cls,
            paper,
            direction=direction,
            lag_ratio=lag_ratio,
            dismiss=dismiss,
            use_override=use_override,
            **kwargs,
        )

    def __init__(
        self,
        paper: Paper,
        *,
        direction: np.ndarray = DOWN,
        lag_ratio: float = 0.3,
        dismiss: bool = False,
        **kwargs: Any,
    ) -> None:
        shift_vec = np.asarray(direction, dtype=float) * 2.0
        anim_cls = FadeOut if dismiss else FadeIn
        paper._sync_submobjects()

        # Intro: back-to-front (last page first, top page last).
        # Dismiss: front-to-back (top page first, last page last).
        ordering = paper.page_groups if dismiss else list(reversed(paper.page_groups))

        anims = [anim_cls(pg, shift=shift_vec) for pg in ordering]
        kwargs.setdefault("run_time", 1.5)
        super().__init__(*anims, lag_ratio=lag_ratio, **kwargs)


class DismissPaper(ShowPaper):
    """Exit animation — syntactic sugar for ``ShowPaper(..., dismiss=True)``."""

    def __new__(
        cls,
        paper: Paper,
        *,
        direction: np.ndarray = DOWN,
        lag_ratio: float = 0.3,
        use_override: bool = True,
        **kwargs: Any,
    ) -> Self:
        return super().__new__(
            cls,
            paper,
            direction=direction,
            lag_ratio=lag_ratio,
            dismiss=True,
            use_override=use_override,
            **kwargs,
        )

    def __init__(
        self,
        paper: Paper,
        *,
        direction: np.ndarray = DOWN,
        lag_ratio: float = 0.3,
        **kwargs: Any,
    ) -> None:
        super().__init__(paper, direction=direction, lag_ratio=lag_ratio, dismiss=True, **kwargs)


class PickPage(Animation):
    """Animate a page sliding out of the stack, then moving to the top/front.

    The target page slides out in *slide_direction*, pauses visibly beside
    the stack, then slides back to position 0 (the front). The remaining
    pages re-settle to fill the gap.

    Parameters
    ----------
    paper
        The Paper mobject containing the stack.
    page_index
        Which page to pick (0 = current top; 1+ = pages behind it).
    slide_direction
        Direction the page slides out before returning to the top. Pass a
        Manim direction vector such as ``RIGHT`` or ``LEFT``.
    overshoot
        How far (Manim units) the page travels out before settling.
    """

    def __new__(
        cls,
        paper: Paper,
        page_index: int = 1,
        *,
        slide_direction: np.ndarray = RIGHT,
        overshoot: float = 3.0,
        use_override: bool = True,
        **kwargs: Any,
    ) -> Self:
        return super().__new__(
            cls,
            paper,
            page_index,
            slide_direction=slide_direction,
            overshoot=overshoot,
            use_override=use_override,
            **kwargs,
        )

    def __init__(
        self,
        paper: Paper,
        page_index: int = 1,
        *,
        slide_direction: np.ndarray = RIGHT,
        overshoot: float = 3.0,
        **kwargs: Any,
    ) -> None:
        if page_index < 0 or page_index >= paper.page_count:
            raise IndexError(f"page_index {page_index} out of range [0, {paper.page_count})")
        self._paper = paper
        self._page_index = page_index
        self._slide_vec = np.asarray(slide_direction, dtype=float) * overshoot
        kwargs.setdefault("run_time", 2.0)
        super().__init__(paper, **kwargs)

    def begin(self) -> None:
        self._page = self._paper.get_page(self._page_index)
        self._start_pos = self._page.get_center().copy()
        self._original_order = self._paper.page_groups
        self._target_order = [
            self._page,
            *(pg for pg in self._original_order if pg is not self._page),
        ]
        self._paper._set_page_order(self._original_order, arrange=False)
        self._page.set_z_index(self._paper.z_index - 1, family=True)

        self._other_pages = [pg for pg in self._target_order if pg is not self._page]
        self._other_pages_start = [pg.get_center().copy() for pg in self._other_pages]
        self._other_pages_end = [
            self._paper._stack_dir * self._paper._stack_offset * i
            for i, pg in enumerate(self._target_order)
            if pg is not self._page
        ]

        self._end_pos = self._paper._stack_dir * self._paper._stack_offset * 0
        self._midpoint = self._start_pos + self._slide_vec
        self._promoted = False
        super().begin()

    def interpolate_mobject(self, alpha: float) -> None:
        t = smooth(alpha)

        if t < 0.5:
            sub_t = t * 2.0
            pos = self._start_pos + (self._midpoint - self._start_pos) * sub_t
        else:
            if not self._promoted:
                self._paper._set_page_order(self._target_order, arrange=False)
                self._promoted = True
            sub_t = (t - 0.5) * 2.0
            pos = self._midpoint + (self._end_pos - self._midpoint) * sub_t

        self._page.move_to(pos)

        settle_t = min(t * 2.0, 1.0)
        for i, pg in enumerate(self._other_pages):
            start = self._other_pages_start[i]
            end = self._other_pages_end[i]
            pg.move_to(start + (end - start) * settle_t)

    def finish(self) -> None:
        self._paper._set_page_order(self._target_order, arrange=False)
        self._page.move_to(self._end_pos)
        for i, pg in enumerate(self._other_pages):
            pg.move_to(self._other_pages_end[i])
        super().finish()
