r"""markdown-it-py plugin -- `\cite{key1, key2}` -> linked alpha tag.

Renders as `<a class="cite" href="#bib-{key}">[Auth23]</a>`. Multiple keys
inside one `\cite{...}` produce a single bracket with separators:
`[Auth23, Smit24]`.

The plugin stashes the cited keys onto ``state.env["citations"]`` so the
notes renderer can emit a per-deck bibliography in citation order.

Unknown keys render with the extra class ``cite-stale`` (mirrors
`slide_ref`) -- the build still produces a usable page that visibly
flags the issue.
"""

import re
from typing import Any

from markdown_it import MarkdownIt
from markdown_it.rules_inline import StateInline

from simplex.web.bibliography import Bibliography

NAME = "cite"
ENV_KEY = "citations"

# `\cite{key1, key2}` -- whitespace permitted inside the braces.
_PATTERN = re.compile(r"\\cite\{([^}]+)\}")
# BibTeX keys are alphanumerics plus a small punctuation set.
_KEY_RE = re.compile(r"^[A-Za-z0-9_:\-./+]+$")


def make_plugin(bibliography: Bibliography | None) -> Any:
    """Return a markdown-it plugin bound to the deck's bibliography."""

    bib = bibliography or Bibliography.empty()

    def plugin(md: MarkdownIt) -> None:
        def rule(state: StateInline, silent: bool) -> bool:
            if state.src[state.pos] != "\\":
                return False
            match = _PATTERN.match(state.src, state.pos)
            if not match:
                return False
            keys = tuple(_clean_keys(match.group(1)))
            if not keys:
                return False
            # Silent / validation mode: callers like `parseLinkLabel` need
            # `state.pos` advanced past the match, otherwise they loop.
            if silent:
                state.pos = match.end()
                return True
            _record_keys(state, keys)
            token = state.push("html_inline", "", 0)
            token.content = _render(keys, bib)
            state.pos = match.end()
            return True

        # Must run before `escape`: markdown-it's escape rule consumes the
        # leading backslash unconditionally, so `\cite{...}` never reaches
        # `link`-level rules. Putting `cite` ahead of `escape` keeps the
        # backslash available to match the LaTeX-style pattern.
        md.inline.ruler.before("escape", NAME, rule)

    return plugin


def _clean_keys(raw: str) -> list[str]:
    out: list[str] = []
    for piece in raw.split(","):
        key = piece.strip()
        if key and _KEY_RE.match(key):
            out.append(key)
    return out


def _record_keys(state: StateInline, keys: tuple[str, ...]) -> None:
    """Append to `state.env[ENV_KEY]` so the renderer can build a bib list."""
    used: list[str] = state.env.setdefault(ENV_KEY, [])
    for key in keys:
        if key not in used:
            used.append(key)


def _render(keys: tuple[str, ...], bib: Bibliography) -> str:
    parts: list[str] = []
    for key in keys:
        if bib.has(key):
            entry = bib.get(key)
            parts.append(
                f'<a class="cite" href="#bib-{_attr(key)}" '
                f'title="{_attr(_title(entry))}">{_text(entry.alpha_key)}</a>'
            )
        else:
            parts.append(
                f'<a class="cite cite-stale" href="#" '
                f'title="Unknown citation key: {_attr(key)}">{_text(key)}?</a>'
            )
    inner = ", ".join(parts)
    return f'<span class="cite-group">[{inner}]</span>'


def _title(entry: Any) -> str:
    title = entry.fields.get("title", entry.key)
    if entry.year is not None:
        return f"{title} ({entry.year})"
    return title


_ATTR = {"&": "&amp;", "<": "&lt;", '"': "&quot;"}
_TEXT = {"&": "&amp;", "<": "&lt;", ">": "&gt;"}


def _attr(s: str) -> str:
    return "".join(_ATTR.get(c, c) for c in s)


def _text(s: str) -> str:
    return "".join(_TEXT.get(c, c) for c in s)
