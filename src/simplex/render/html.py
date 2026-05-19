"""Render ``slides.html`` for one deck from the reconciled main/sub manifest.

Why we keep a custom template (instead of ``manim_slides.convert.RevealJS``):

The template at ``web/templates/revealjs.html.j2`` carries a polished
RevealJS host -- postMessage bridge to the parent ``deck.html``, touch tap
zones, disabled RevealJS layout (so videos fill the iframe natively),
custom progress bar styling via CSS variables. The manim-slides default
template doesn't have any of that. We do still use
``manim_slides.convert.PDF`` / ``PowerPoint`` for those formats; they have
no custom layout requirements.

The web palette is injected as a ``<style>:root {…}</style>`` block at the
top of ``<head>`` (theme defaults + per-deck overrides via
``DeckConfig.resolved_web_palette()``). A per-deck ``[web] custom_css_path``
is appended verbatim as a second ``<style>`` block.
"""

import shutil
from dataclasses import dataclass
from pathlib import Path

from jinja2 import Environment, PackageLoader, select_autoescape

from simplex.deck.config import DeckConfig
from simplex.manifest import DeckManifest, Subsection
from simplex.theme.web_css import render_web_css


@dataclass(frozen=True, slots=True)
class _SubView:
    name: str
    section_type: str
    video_href: str | None


@dataclass(frozen=True, slots=True)
class _MainView:
    index: int
    scene: str
    name: str
    subsections: tuple[_SubView, ...]


def _env() -> Environment:
    return Environment(
        loader=PackageLoader("simplex.web", "templates"),
        autoescape=select_autoescape(["html", "j2"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )


def _copy_segments(manifest: DeckManifest, dest_dir: Path) -> list[_MainView]:
    """Copy every subsection video into ``dest_dir/segments/`` with stable names."""
    seg_dir = dest_dir / "segments"
    out: list[_MainView] = []
    for main in manifest.main_slides:
        sub_views: list[_SubView] = []
        for sub_idx, sub in enumerate(main.subsections):
            sub_views.append(
                _SubView(
                    name=sub.name,
                    section_type=sub.section_type.value,
                    video_href=_copy_one(sub, main.index, sub_idx, seg_dir, dest_dir),
                )
            )
        out.append(
            _MainView(
                index=main.index,
                scene=main.scene,
                name=main.name,
                subsections=tuple(sub_views),
            )
        )
    return out


def _copy_one(
    sub: Subsection,
    main_idx: int,
    sub_idx: int,
    seg_dir: Path,
    dest_dir: Path,
) -> str | None:
    if sub.video is None or not sub.video.exists():
        return None
    seg_dir.mkdir(parents=True, exist_ok=True)
    target = seg_dir / f"{main_idx:04d}_{sub_idx:02d}.mp4"
    if not target.exists() or target.stat().st_mtime < sub.video.stat().st_mtime:
        shutil.copy2(sub.video, target)
    return target.relative_to(dest_dir).as_posix()


def render_html(
    deck: DeckConfig,
    manifest: DeckManifest,
    *,
    output_dir: Path,
    static_prefix: str,
    watch: bool = False,
) -> Path:
    """Write ``output_dir/slides.html`` and copy its video segments.

    `watch=True` includes an SSE client snippet that listens to
    `/_simplex/events` for live reload (used by `simplex serve --watch`).
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    main_views = _copy_segments(manifest, output_dir)
    palette_css = render_web_css(deck.resolved_web_palette())
    deck_custom_css = ""
    if deck.web.custom_css_path is not None:
        candidate = deck.path / deck.web.custom_css_path
        if candidate.exists():
            deck_custom_css = candidate.read_text(encoding="utf-8")

    template = _env().get_template("revealjs.html.j2")
    html = template.render(
        deck=deck,
        main_slides=main_views,
        main_slide_count=len(main_views),
        static_prefix=static_prefix.rstrip("/"),
        palette_css=palette_css,
        deck_custom_css=deck_custom_css,
        transition=deck.web.transition,
        show_slide_number=deck.web.show_slide_number,
        show_clock=deck.web.show_clock,
        watch=watch,
    )
    out = output_dir / "slides.html"
    out.write_text(html, encoding="utf-8")
    return out
