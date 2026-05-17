r"""Render a deck's notes.md (or a raw markdown string) to academic-style HTML.

Pipeline:

1. markdown-it (commonmark) + plugins:
   - ``dollarmath_plugin``  -- ``$...$`` / ``$$...$$`` -> KaTeX-friendly
     ``\(...\)`` / ``\[...\]``.
   - ``footnote_plugin``    -- ``^[note]`` inline notes (Tufte sidenotes).
   - ``anchors_plugin``     -- heading anchors for deep linking.
   - ``slide_ref``          -- ``[slide:N]`` -> in-page clickable jumps.
   - ``cite``               -- ``\cite{key1,key2}`` -> alpha-tag bibliography
     links; cited keys collected on ``state.env["citations"]``.
2. Pygments syntax highlight for fenced code blocks (DarculaStyle).
3. Post-process footnote HTML into Tufte sidenote markup
   (`web/sidenotes.py`).
4. Append the rendered bibliography (``<ol class="bib-list">``) when a
   ``Bibliography`` was supplied and any keys were cited.

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
from simplex.web import callouts, equations, sidenotes
from simplex.web.bibliography import Bibliography
from simplex.web.citations import ENV_KEY as _CITE_ENV_KEY
from simplex.web.citations import make_plugin as cite_plugin
from simplex.web.refs import make_plugin as ref_plugin
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


def _make(
    slide_count: int | None = None,
    bibliography: Bibliography | None = None,
) -> MarkdownIt:
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
    # `inline=True` enables `^[note]` inline footnotes -- post-processed into
    # Tufte sidenotes by `sidenotes.transform`.
    md.use(footnote_plugin, inline=True, move_to_end=True)
    md.use(anchors_plugin, max_level=3)
    md.use(slide_ref_plugin(slide_count=slide_count))
    md.use(cite_plugin(bibliography))
    md.use(ref_plugin())
    return md


def render_text(
    markdown: str,
    *,
    slide_count: int | None = None,
    bibliography: Bibliography | None = None,
) -> str:
    """Render a markdown string to academic-style HTML.

    Pass `bibliography` to enable `\\cite{key}` -> linked alpha tags and a
    trailing ``<section class="bibliography">``. When omitted, ``\\cite{}``
    markers render as the literal `[key?]` "stale" tags.
    """
    md = _make(slide_count=slide_count, bibliography=bibliography)
    env: dict[str, Any] = {}
    body = md.render(markdown, env)
    body = sidenotes.transform(body)
    # Equations first so the labels they emit are visible to the callouts
    # pass, which resolves every `\ref{...}` placeholder in one walk.
    body, eq_labels = equations.transform(body)
    # Callouts after sidenotes so blockquote-shaped sidenotes (unlikely but
    # possible) don't get mis-rewritten; before bibliography so `\ref{}`
    # placeholders that point at callouts (or equations) can be resolved
    # while we're still walking the body.
    body = callouts.transform(body, extra_labels=eq_labels)
    if bibliography is not None:
        used = tuple(env.get(_CITE_ENV_KEY, []))
        if used:
            body += bibliography.to_html(used)
    return body


def render(
    notes_md: Path,
    *,
    slide_count: int | None = None,
    bibliography: Bibliography | None = None,
) -> str:
    """Render a notes.md file to HTML."""
    return render_text(
        notes_md.read_text(encoding="utf-8"),
        slide_count=slide_count,
        bibliography=bibliography,
    )
