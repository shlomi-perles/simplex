"""Minimal pure-Python BibTeX parser.

A `.bib` file is a sequence of `@type{key, field = value, ...}` entries.
This module turns one such file into a sequence of
``(key, entry_type, fields)`` triples; `bibliography.py` consumes those
and assembles `BibEntry` / `Bibliography` models on top.

Why pure-Python (not `bibtexparser`):

- We need a tiny, predictable subset: brace- or quote-delimited field values,
  comma-separated fields, the `@string` / `@preamble` / `@comment` skip set.
- Hand-rolling that takes <120 LOC; we don't pull in another dep for it.

Open issues we deliberately don't handle (and don't need for deck notes):

- `@string{x = "y"}` substitution -- treats string aliases as opaque tokens.
- Concatenation with `#` -- left as-is; doesn't appear in our refs.bib files.
"""

import re
from collections.abc import Iterator

_ENTRY_HEAD = re.compile(r"@(?P<type>\w+)\s*\{\s*(?P<key>[^,\s]+)\s*,", re.IGNORECASE)
_SKIP_TYPES = {"string", "preamble", "comment"}


def parse(text: str) -> Iterator[tuple[str, str, dict[str, str]]]:
    """Yield `(key, entry_type, fields)` triples from a `.bib` document."""
    cleaned = "\n".join(line for line in text.splitlines() if not line.lstrip().startswith("%"))
    pos = 0
    while pos < len(cleaned):
        match = _ENTRY_HEAD.search(cleaned, pos)
        if not match:
            return
        entry_type = match.group("type")
        if entry_type.lower() in _SKIP_TYPES:
            pos = _skip_balanced(cleaned, match.end() - 1)
            continue
        body_end = _find_close_brace(cleaned, match.end())
        if body_end < 0:
            return
        yield match.group("key"), entry_type, _parse_fields(cleaned[match.end() : body_end])
        pos = body_end + 1


def _find_close_brace(text: str, start: int) -> int:
    """Return the index of the matching `}` starting from `start` (depth 1),
    or -1 if unterminated. Skips over `"..."` quoted spans (BibTeX has no
    backslash escapes inside quotes)."""
    depth = 1
    i = start
    while i < len(text):
        ch = text[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return i
        elif ch == '"':
            i = text.find('"', i + 1)
            if i < 0:
                return -1
        i += 1
    return -1


def _skip_balanced(text: str, brace_pos: int) -> int:
    """Return the index *after* a `{...}` group that starts at `brace_pos`."""
    end = _find_close_brace(text, brace_pos + 1)
    return end + 1 if end >= 0 else len(text)


def _parse_fields(body: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    i = 0
    while i < len(body):
        while i < len(body) and body[i] in " \t\r\n,":
            i += 1
        if i >= len(body):
            break
        name_start = i
        while i < len(body) and body[i] not in "= \t\r\n":
            i += 1
        name = body[name_start:i].lower()
        if not name:
            break
        while i < len(body) and body[i] != "=":
            i += 1
        i += 1
        while i < len(body) and body[i] in " \t\r\n":
            i += 1
        if i >= len(body):
            break
        value, i = _read_value(body, i)
        fields[name] = value
    return fields


def _read_value(text: str, start: int) -> tuple[str, int]:
    """Read one field value (braced, quoted, or bare token). Returns the
    value plus the index of the next unread character."""
    if text[start] == "{":
        end = _find_close_brace(text, start + 1)
        if end < 0:
            return text[start + 1 :].strip(), len(text)
        return _normalise_ws(text[start + 1 : end]), end + 1
    if text[start] == '"':
        end = text.find('"', start + 1)
        if end < 0:
            return text[start + 1 :].strip(), len(text)
        return _normalise_ws(text[start + 1 : end]), end + 1
    j = start
    while j < len(text) and text[j] not in ",\n}":
        j += 1
    return text[start:j].strip(), j


def _normalise_ws(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def unbrace(s: str) -> str:
    """Drop the outer `{...}` braces BibTeX uses to protect title casing.

    Public because `bibliography.py` calls it when rendering field values
    (titles, journals) without dragging in regex internals.
    """
    return re.sub(r"[{}]", "", s)
