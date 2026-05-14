"""Emit ``slides.html`` directly from manim-slides' rendered artifacts.

We deliberately bypass ``manim-slides convert --to=html`` so that:

- The RevealJS init config is ours (touch handling, embedded mode, reduced
  motion).
- The postMessage bridge to the parent page is part of the page, not bolted
  on via DOM patches.
- A manim-slides minor bump cannot regress the viewer.

The template lives at ``src/simplex/web/templates/revealjs.html.j2``; video
segments are copied next to it under ``segments/``.
"""

import shutil
from pathlib import Path

from jinja2 import Environment, PackageLoader, select_autoescape

from simplex.deck.config import DeckConfig
from simplex.render.manifest import DeckManifest, SlideRef


class _SlideAsset:
    """View-model passed to the Jinja template, one per playable slide."""

    __slots__ = ("duration_s", "index", "notes", "scene", "title", "video")

    def __init__(
        self,
        slide: SlideRef,
        video_href: str | None,
    ) -> None:
        self.index = slide.index
        self.scene = slide.scene
        self.title = slide.title or ""
        self.video = video_href
        self.duration_s = slide.duration_s
        self.notes = slide.notes or ""


def _env() -> Environment:
    return Environment(
        loader=PackageLoader("simplex.web", "templates"),
        autoescape=select_autoescape(["html", "j2"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )


def _copy_segments(manifest: DeckManifest, dest_dir: Path) -> list[_SlideAsset]:
    seg_dir = dest_dir / "segments"
    assets: list[_SlideAsset] = []
    for slide in manifest.slides:
        video_href: str | None = None
        if slide.video_paths:
            src = slide.video_paths[0]
            if src.exists():
                seg_dir.mkdir(parents=True, exist_ok=True)
                # Stable name -- index-padded so lexical sort matches play order.
                target = seg_dir / f"{slide.index:04d}.mp4"
                if not target.exists() or target.stat().st_mtime < src.stat().st_mtime:
                    shutil.copy2(src, target)
                video_href = target.relative_to(dest_dir).as_posix()
        assets.append(_SlideAsset(slide, video_href))
    return assets


def render_html(
    deck: DeckConfig,
    manifest: DeckManifest,
    *,
    output_dir: Path,
    static_prefix: str,
) -> Path:
    """Write ``output_dir/slides.html`` and copy its video segments."""
    output_dir.mkdir(parents=True, exist_ok=True)
    assets = _copy_segments(manifest, output_dir)
    env = _env()
    template = env.get_template("revealjs.html.j2")
    html = template.render(
        deck=deck,
        slides=assets,
        static_prefix=static_prefix.rstrip("/"),
        slide_count=len(assets),
    )
    out = output_dir / "slides.html"
    out.write_text(html, encoding="utf-8")
    return out
