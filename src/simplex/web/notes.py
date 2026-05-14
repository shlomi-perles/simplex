"""Render a deck's notes.md (or a raw markdown string) to HTML."""

from pathlib import Path

from markdown_it import MarkdownIt
from mdit_py_plugins.anchors import anchors_plugin
from mdit_py_plugins.dollarmath import dollarmath_plugin
from mdit_py_plugins.footnote import footnote_plugin

from simplex.web.slide_ref import make_plugin as slide_ref_plugin


def _make(slide_count: int | None = None) -> MarkdownIt:
    md = MarkdownIt("commonmark", {"html": False, "linkify": True, "typographer": True})
    md.enable("table")
    md.use(dollarmath_plugin, allow_labels=True)
    md.use(footnote_plugin)
    md.use(anchors_plugin, max_level=3)
    md.use(slide_ref_plugin(slide_count=slide_count))
    return md


def render_text(markdown: str, *, slide_count: int | None = None) -> str:
    """Render a markdown string to HTML."""
    return _make(slide_count=slide_count).render(markdown)


def render(notes_md: Path, *, slide_count: int | None = None) -> str:
    """Render a notes.md file to HTML."""
    return render_text(notes_md.read_text(encoding="utf-8"), slide_count=slide_count)
