r"""markdown-it-py plugin -- `\ref{id}` / `\autoref{id}` placeholders.

Emits ``<a class="ref" data-simplex-ref="id" href="#id">id</a>``. The
callouts post-processor (`web/callouts.py`) resolves the placeholder to
the proper display label (`Theorem 3.1`) once block IDs are known.

Mirrors `\cite{...}`: registered *before* `escape` so the leading
backslash survives, advances `state.pos` in silent mode so caller
loops (`parseLinkLabel`, used by inline footnotes) terminate.
"""

import re
from typing import Any

from markdown_it import MarkdownIt
from markdown_it.rules_inline import StateInline

NAME = "ref"

# `\ref{id}` / `\autoref{id}` -- id can include letters, digits, dashes,
# dots, colons, slashes.
_PATTERN = re.compile(r"\\(?:auto)?ref\{([A-Za-z0-9_:\-./]+)\}")


def make_plugin() -> Any:
    """Return a markdown-it plugin emitting cross-reference placeholders."""

    def plugin(md: MarkdownIt) -> None:
        def rule(state: StateInline, silent: bool) -> bool:
            if state.src[state.pos] != "\\":
                return False
            match = _PATTERN.match(state.src, state.pos)
            if not match:
                return False
            if silent:
                state.pos = match.end()
                return True
            ref_id = match.group(1)
            token = state.push("html_inline", "", 0)
            token.content = (
                f'<a class="ref" data-simplex-ref="{_attr(ref_id)}" '
                f'href="#{_attr(ref_id)}">{_text(ref_id)}</a>'
            )
            state.pos = match.end()
            return True

        md.inline.ruler.before("escape", NAME, rule)

    return plugin


_ATTR = {"&": "&amp;", "<": "&lt;", '"': "&quot;"}
_TEXT = {"&": "&amp;", "<": "&lt;", ">": "&gt;"}


def _attr(s: str) -> str:
    return "".join(_ATTR.get(c, c) for c in s)


def _text(s: str) -> str:
    return "".join(_TEXT.get(c, c) for c in s)
