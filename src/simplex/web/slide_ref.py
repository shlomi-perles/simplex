"""markdown-it-py plugin -- ``[slide:label]`` => clickable jump anchor.

Renders as ``<a href="#" class="slide-ref" data-slide="{index}">label</a>``.
The parent viewer.js (see ``web/static/viewer.js``) binds clicks and forwards
``{type: 'simplex.goto', idx: index}`` to the iframe. Numeric ``[slide:2]``
refs are still supported, but label refs such as ``[slide:key-idea]`` are
preferred because they survive slide reordering.
"""

import re
from collections.abc import Mapping
from typing import Any

from markdown_it import MarkdownIt
from markdown_it.rules_inline import StateInline

NAME = "slide_ref"
_PATTERN = re.compile(r"\[slide:([^\]]+)\]")
_SPACE = re.compile(r"\s+")

SlideRefMap = Mapping[str, tuple[int, str]]


def label_key(label: str) -> str:
    """Normalize human slide labels for stable note refs."""
    value = label.strip().lower().replace("_", "-")
    value = _SPACE.sub("-", value)
    value = re.sub(r"[^a-z0-9:./-]+", "", value)
    return re.sub(r"-{2,}", "-", value).strip("-")


def make_plugin(
    slide_count: int | None = None,
    slide_refs: SlideRefMap | None = None,
) -> Any:
    """Return a markdown-it plugin bound to a slide count and labels."""
    refs = {label_key(k): v for k, v in (slide_refs or {}).items()}

    def plugin(md: MarkdownIt) -> None:
        def rule(state: StateInline, silent: bool) -> bool:
            if state.src[state.pos] != "[":
                return False
            match = _PATTERN.match(state.src, state.pos)
            if not match:
                return False
            # Silent / validation mode: must still advance `state.pos` past
            # the match so callers like `parseLinkLabel` don't loop forever.
            if silent:
                state.pos = match.end()
                return True

            raw = match.group(1).strip()
            target = refs.get(label_key(raw))
            if target is None and raw.isdigit():
                n = int(raw)
                target = (n, raw)
            if target is None:
                n = 0
                label = raw
                stale = True
            else:
                n, label = target
                stale = slide_count is not None and (n < 1 or n > slide_count)

            token = state.push("html_inline", "", 0)
            classes = "slide-ref" + (" slide-ref-stale" if stale else "")
            title = "Slide out of range" if stale else f"Jump to slide {label}"
            token.content = (
                f'<a href="#" class="{classes}" data-slide="{n}" '
                f'role="button" aria-label="{_attr(title)}" title="{_attr(title)}">'
                f"{_text(label)}</a>"
            )
            state.pos = match.end()
            return True

        md.inline.ruler.before("link", NAME, rule)

    return plugin


_ATTR = {"&": "&amp;", "<": "&lt;", '"': "&quot;"}
_TEXT = {"&": "&amp;", "<": "&lt;", ">": "&gt;"}


def _attr(s: str) -> str:
    return "".join(_ATTR.get(c, c) for c in s)


def _text(s: str) -> str:
    return "".join(_TEXT.get(c, c) for c in s)
