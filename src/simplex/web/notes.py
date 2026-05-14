"""Render a deck's notes.md to HTML with KaTeX-ready math."""

from pathlib import Path

from markdown_it import MarkdownIt
from mdit_py_plugins.anchors import anchors_plugin
from mdit_py_plugins.dollarmath import dollarmath_plugin
from mdit_py_plugins.footnote import footnote_plugin


def _make() -> MarkdownIt:
    md = MarkdownIt("commonmark", {"html": False, "linkify": True, "typographer": True})
    md.enable("table")
    md.use(dollarmath_plugin, allow_labels=True)
    md.use(footnote_plugin)
    md.use(anchors_plugin, max_level=3)
    return md


def render(notes_md: Path) -> str:
    return _make().render(notes_md.read_text(encoding="utf-8"))
