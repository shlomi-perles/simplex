"""BibTeX -> biblatex-alpha citation keys + HTML bibliography.

`bibtex.py` does the parsing; this module owns the data model and the
rendered output.

Public surface (see `simplex/web/README.md`):

- `Bibliography.parse(text)` / `.load(path)` -- read a `.bib` file.
- `Bibliography.get(key)` -- retrieve an entry, raises if missing.
- `Bibliography.has(key)` -- existence check (used by the citations plugin).
- `Bibliography.to_html(used)` -- ordered <ol> of the cited entries, in the
  order they were first referenced. Pass an empty tuple to suppress.

Alpha labels follow `biblatex`'s `alpha` style:

    1 author  -> 3 letters of last name           ("Hou00")
    2-3       -> 1 letter of each last name       ("KB15", "DHS11")
    4+        -> 3 letters of first three + "+"   ("ABG+23")

followed by the last two digits of the year (or `??` if unknown).
"""

import re
from pathlib import Path
from typing import Self

from pydantic import BaseModel, ConfigDict

from simplex.web import bibtex


class Author(BaseModel):
    """A single author. `last` is what appears in alpha labels."""

    model_config = ConfigDict(frozen=True)

    last: str
    first: str = ""

    @classmethod
    def parse(cls, raw: str) -> Self:
        """Parse a BibTeX author token (`Last, First` or `First Last`)."""
        raw = bibtex.unbrace(raw.strip())
        if "," in raw:
            last, first = raw.split(",", 1)
            return cls(last=last.strip(), first=first.strip())
        parts = raw.split()
        if len(parts) == 1:
            return cls(last=parts[0])
        return cls(last=parts[-1], first=" ".join(parts[:-1]))

    @property
    def display(self) -> str:
        """`F. Last`-style initials for the bibliography list."""
        if not self.first:
            return self.last
        initials = " ".join(f"{p[0]}." for p in self.first.split() if p)
        return f"{initials} {self.last}".strip()


class BibEntry(BaseModel):
    """A single bibliography entry. The field bag stays a plain dict because
    BibTeX's field set is open."""

    model_config = ConfigDict(frozen=True)

    key: str
    entry_type: str
    fields: dict[str, str]
    authors: tuple[Author, ...]
    year: int | None
    alpha_key: str

    @classmethod
    def make(cls, key: str, entry_type: str, fields: dict[str, str]) -> Self:
        authors = _parse_authors(fields.get("author") or fields.get("editor") or "")
        year = _parse_year(fields.get("year", ""))
        return cls(
            key=key,
            entry_type=entry_type.lower(),
            fields=fields,
            authors=authors,
            year=year,
            alpha_key=_alpha_key(authors, year),
        )

    def render_html(self) -> str:
        """Emit one <li> for the bibliography list.

        The alpha-key marker (e.g. `[KB15]`) is rendered as an inline
        `<span class="bib-marker">`, not a CSS counter, so the printed
        bullet matches the inline `[KB15]` citation chip.
        """
        parts: list[str] = []
        if self.authors:
            parts.append(_join_authors(self.authors))
        if title := self.fields.get("title"):
            # Wrap titles in quotes (academic convention). Joining with ", "
            # yields the canonical `Authors, "Title," Venue, Year.` shape.
            parts.append(f"&ldquo;{_escape_html(bibtex.unbrace(title))}&rdquo;")
        if venue := self._venue_html():
            parts.append(venue)
        if self.year is not None:
            parts.append(str(self.year))
        body = ", ".join(parts)
        if link := self._link_html():
            body = f"{body} {link}"
        marker = f'<span class="bib-marker">[{_escape_html(self.alpha_key)}]</span>'
        return f'<li id="bib-{_escape_html(self.key)}" class="bib-entry">{marker} {body}.</li>'

    def _venue_html(self) -> str:
        for field in ("journal", "booktitle", "publisher", "school", "institution"):
            if value := self.fields.get(field):
                return f"<em>{_escape_html(bibtex.unbrace(value))}</em>"
        return ""

    def _link_html(self) -> str:
        for field in ("doi", "url"):
            value = self.fields.get(field)
            if not value:
                continue
            value = bibtex.unbrace(value)
            href = value if field == "url" else f"https://doi.org/{value}"
            return (
                f'<a class="bib-link" href="{_escape_html(href)}" '
                f'rel="noopener" target="_blank">[link]</a>'
            )
        return ""


class Bibliography(BaseModel):
    """Parsed .bib file. `entries` is keyed by the BibTeX cite key."""

    entries: dict[str, BibEntry]

    @classmethod
    def parse(cls, text: str) -> Self:
        """Parse a BibTeX document. Duplicate keys keep the first definition;
        the citations plugin marks unknown keys as stale."""
        parsed: dict[str, BibEntry] = {}
        for key, entry_type, fields in bibtex.parse(text):
            if key in parsed:
                continue
            parsed[key] = BibEntry.make(key, entry_type, fields)
        return cls(entries=parsed)

    @classmethod
    def load(cls, path: Path) -> Self:
        return cls.parse(path.read_text(encoding="utf-8"))

    @classmethod
    def empty(cls) -> Self:
        return cls(entries={})

    def has(self, key: str) -> bool:
        return key in self.entries

    def get(self, key: str) -> BibEntry:
        return self.entries[key]

    def to_html(self, used: tuple[str, ...]) -> str:
        """Render an ordered list of the cited entries, in citation order."""
        seen: set[str] = set()
        ordered: list[BibEntry] = []
        for key in used:
            if key in seen or key not in self.entries:
                continue
            seen.add(key)
            ordered.append(self.entries[key])
        if not ordered:
            return ""
        items = "\n".join(e.render_html() for e in ordered)
        return (
            '<section class="bibliography" aria-labelledby="bib-heading">'
            '<h2 id="bib-heading">References</h2>'
            f'<ol class="bib-list">\n{items}\n</ol>'
            "</section>"
        )


# ---------------------------------------------------------------------------
# Author / alpha-key helpers
# ---------------------------------------------------------------------------


def _parse_authors(raw: str) -> tuple[Author, ...]:
    if not raw:
        return ()
    parts = re.split(r"\s+and\s+", raw, flags=re.IGNORECASE)
    return tuple(Author.parse(p) for p in parts if p.strip())


def _parse_year(raw: str) -> int | None:
    if not raw:
        return None
    match = re.search(r"\d{4}", raw)
    return int(match.group(0)) if match else None


def _alpha_key(authors: tuple[Author, ...], year: int | None) -> str:
    """biblatex-alpha label. Empty author list -> `Anon` prefix."""
    suffix = f"{year % 100:02d}" if year is not None else "??"
    if not authors:
        return f"Anon{suffix}"
    initials = [_first_letter(a.last) for a in authors]
    match len(initials):
        case 1:
            prefix = (initials[0] + _initial_pad(authors[0].last))[:3]
        case 2 | 3:
            prefix = "".join(initials)
        case _:
            prefix = "".join(initials[:3]) + "+"
    return f"{prefix}{suffix}"


def _first_letter(s: str) -> str:
    for ch in s:
        if ch.isalpha():
            return ch.upper()
    return "?"


def _initial_pad(last: str) -> str:
    """For single-author keys, take chars 2-3 of the last name (lowercased)."""
    letters = [c for c in last if c.isalpha()]
    return "".join(letters[1:3]).lower()


def _join_authors(authors: tuple[Author, ...]) -> str:
    """`A. Smith, B. Jones, and C. Lee`."""
    names = [_escape_html(a.display) for a in authors]
    match len(names):
        case 0:
            return ""
        case 1:
            return names[0]
        case 2:
            return f"{names[0]} and {names[1]}"
        case _:
            head = ", ".join(names[:-1])
            return f"{head}, and {names[-1]}"


_ESCAPE = {"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;"}


def _escape_html(s: str) -> str:
    return "".join(_ESCAPE.get(c, c) for c in s)
