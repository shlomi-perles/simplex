"""Render a deck's notes.md (or a raw markdown string) to HTML.

Math (``$...$`` / ``$$...$$``) is rewritten with KaTeX-friendly ``\\(...\\)``
and ``\\[...\\]`` delimiters so katex auto-render (loaded in base.html) can
typeset it client-side. Fenced code blocks are highlighted server-side with
Pygments using the same DarculaStyle the video engine uses, so notes match
the slides visually.
"""

from pathlib import Path
from typing import Any

from markdown_it import MarkdownIt
from mdit_py_plugins.anchors import anchors_plugin
from mdit_py_plugins.dollarmath import dollarmath_plugin
from mdit_py_plugins.footnote import footnote_plugin
from pygments import highlight as _pyg_highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name, guess_lexer
from pygments.util import ClassNotFound

from simplex.theme.pygments_style import DarculaStyle
from simplex.web.slide_ref import make_plugin as slide_ref_plugin


def _math_renderer(content: str, options: dict[str, Any]) -> str:
    content = content.strip()
    if options.get("display_mode"):
        return f"\\[{content}\\]"
    return f"\\({content}\\)"


# `nowrap=True` strips the Pygments <div><pre> wrap so markdown-it's own
# <pre><code> is the only wrap. The Darcula background lives on
# `.deck-notes pre` in simplex.css.
_FORMATTER = HtmlFormatter(nowrap=True, noclasses=True, style=DarculaStyle)


def _highlight(code: str, lang: str, _attrs: str) -> str:
    try:
        lexer = get_lexer_by_name(lang) if lang else guess_lexer(code)
    except ClassNotFound:
        return ""  # markdown-it falls back to its default <pre><code>
    return _pyg_highlight(code, lexer, _FORMATTER)


def _make(slide_count: int | None = None) -> MarkdownIt:
    md = MarkdownIt(
        "commonmark",
        {
            "html": False,
            "linkify": True,
            "typographer": True,
            "highlight": _highlight,
        },
    )
    md.enable("table")
    md.use(dollarmath_plugin, allow_labels=True, renderer=_math_renderer)
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
