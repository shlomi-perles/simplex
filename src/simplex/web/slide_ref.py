"""markdown-it-py plugin -- ``[slide:N]`` => clickable jump anchor.

Renders as ``<a href="#" class="slide-ref" data-slide="{N-1}">N</a>``. The
parent viewer.js (see ``web/static/viewer.js``) binds clicks and forwards
``{type: 'simplex.goto', idx: N-1}`` to the iframe.

If ``slide_count`` is provided and N is out of range, the anchor is emitted
with the extra class ``slide-ref-stale`` so the build flags it visually
without breaking the page.
"""

import re
from typing import Any

from markdown_it import MarkdownIt
from markdown_it.rules_inline import StateInline

NAME = "slide_ref"
_PATTERN = re.compile(r"\[slide:(\d+)\]")


def make_plugin(slide_count: int | None = None) -> Any:
    """Return a markdown-it plugin bound to a slide count for validation."""

    def plugin(md: MarkdownIt) -> None:
        def rule(state: StateInline, silent: bool) -> bool:
            if state.src[state.pos] != "[":
                return False
            match = _PATTERN.match(state.src, state.pos)
            if not match:
                return False
            if silent:
                return True
            n = int(match.group(1))
            stale = slide_count is not None and (n < 1 or n > slide_count)
            token = state.push("html_inline", "", 0)
            classes = "slide-ref" + (" slide-ref-stale" if stale else "")
            title = "Slide out of range" if stale else f"Jump to slide {n}"
            token.content = (
                f'<a href="#" class="{classes}" data-slide="{n - 1}" '
                f'role="button" aria-label="{title}" title="{title}">{n}</a>'
            )
            state.pos = match.end()
            return True

        md.inline.ruler.before("link", NAME, rule)

    return plugin
