r"""Theorem-environment callouts + ``\ref{}`` resolution.

Rewrites ``<blockquote><p><strong>Theorem.</strong>\label{thm:x}...</p></blockquote>``
and the older numbered ``<strong>Theorem 3.1.</strong>`` shape into
colour-coded, anchorable ``<aside>`` blocks:

    <aside class="callout callout-theorem" id="thm:x">
      <span class="callout-tag">Theorem 1.</span> Let f...
    </aside>

Recognised types (case-insensitive): **theorem, lemma, proposition,
corollary, claim, fact, definition, example, remark, proof, observation,
note, conjecture**. Anything else stays a normal blockquote.

Also resolves the placeholders emitted by `web/refs.py`:

    <a class="ref" data-simplex-ref="thm:x" href="#thm:x">
      thm:x
    </a>
        |
        v
    <a class="ref" href="#thm:x">Theorem 1</a>

Unknown ref ids get the ``ref-stale`` class (same convention as
``cite-stale`` / ``slide-ref-stale``).

Pure HTML transformation -- the markdown-it pipeline stays untouched.
"""

import re
from collections import defaultdict
from collections.abc import Mapping

# Types we colour-code. Order matters only for matching priority -- longer
# names first so "Proposition" beats a hypothetical "Prop" prefix.
_TYPES: tuple[str, ...] = (
    "Proposition",
    "Conjecture",
    "Definition",
    "Observation",
    "Corollary",
    "Theorem",
    "Example",
    "Lemma",
    "Remark",
    "Proof",
    "Claim",
    "Fact",
    "Note",
)
_TYPES_LC: frozenset[str] = frozenset(t.lower() for t in _TYPES)
_TYPE_ALT = "|".join(_TYPES)
_UNNUMBERED_TYPES = frozenset({"proof"})

# Match a leading `<p><strong>Theorem 3.1.</strong>` inside a blockquote.
# The number is optional (``Proof.`` / ``Remark.`` may stand alone). We
# capture the trailing period(s) too so the tag prints faithfully.
_TAG_RE = re.compile(
    rf"<p>\s*<strong>\s*(?P<type>{_TYPE_ALT})"
    r"(?:\s+(?P<num>\d+(?:\.\d+)*))?\s*\.\s*</strong>\s*",
    re.IGNORECASE,
)
_LABEL_RE = re.compile(r"\\label\{(?P<label>[A-Za-z0-9_:\-./]+)\}")
_BLOCKQUOTE_RE = re.compile(r"<blockquote>(?P<body>.*?)</blockquote>", re.DOTALL)
_REF_RE = re.compile(
    r'<a class="ref" data-simplex-ref="(?P<id>[^"]+)" '
    r'href="#(?P=id)">(?P<fallback>[^<]+)</a>'
)

type LabelMap = Mapping[str, str | tuple[str, str]]


def transform(html: str, *, extra_labels: LabelMap | None = None) -> str:
    """Rewrite theorem-style blockquotes and resolve `\\ref{}` placeholders.

    `extra_labels` lets other passes (e.g. `equations.transform`) seed the
    label map: any id present there is reachable via `\\ref{id}` and
    rendered with the supplied display string. Callout ids overwrite
    extra labels of the same name (rare, but the callout is the more
    specific definition).

    Two-pass:
      1. Walk every blockquote, detect callout type, rewrite to `<aside>`,
         and record the label map (`"theorem-3-1" -> "Theorem 3.1"`).
      2. Walk every `<a class="ref">` placeholder and substitute the
         display label, combining `extra_labels` with the callout map.
    """
    labels: dict[str, tuple[str, str]] = {}
    for key, value in (extra_labels or {}).items():
        labels[key] = value if isinstance(value, tuple) else (key, value)

    # Auto-numbering for unnumbered callouts. Keyed by lowercase type, which
    # mirrors LaTeX's independent theorem counters.
    counters: dict[str, int] = defaultdict(int)

    def rewrite_blockquote(match: re.Match[str]) -> str:
        body = match.group("body")
        tag_match = _TAG_RE.search(body)
        if not tag_match:
            return match.group(0)
        # Bail out if the tag isn't actually at the top of the blockquote --
        # we don't want to rewrite a quoted theorem reference appearing
        # mid-paragraph as a callout.
        prefix = body[: tag_match.start()].strip()
        if prefix:
            return match.group(0)

        kind = tag_match.group("type").lower()
        if kind not in _TYPES_LC:
            return match.group(0)

        num = tag_match.group("num")
        if num:
            slug_num = num.replace(".", "-")
            display = f"{tag_match.group('type').title()} {num}"
        elif kind in _UNNUMBERED_TYPES:
            counters[kind] += 1
            slug_num = str(counters[kind])
            display = tag_match.group("type").title()
        else:
            counters[kind] += 1
            slug_num = str(counters[kind])
            display = f"{tag_match.group('type').title()} {slug_num}"

        generated_id = f"{kind}-{slug_num}"
        label_ids = _LABEL_RE.findall(body)
        block_id = label_ids[0] if label_ids else generated_id
        labels[generated_id] = (block_id, display)
        for label_id in label_ids:
            labels[label_id] = (block_id, display)

        tag_html = f'<span class="callout-tag">{display}.</span> '
        new_body = body[: tag_match.start()] + "<p>" + tag_html + body[tag_match.end() :]
        new_body = _LABEL_RE.sub("", new_body)
        return f'<aside class="callout callout-{kind}" id="{_attr(block_id)}" role="note">{new_body}</aside>'

    out = _BLOCKQUOTE_RE.sub(rewrite_blockquote, html)

    def resolve_ref(match: re.Match[str]) -> str:
        ref_id = match.group("id")
        if ref_id in labels:
            target, display = labels[ref_id]
            return f'<a class="ref" href="#{_attr(target)}">{_text(display)}</a>'
        # Slide refs / external IDs may legitimately not be in the label
        # map; mark unresolved ones as stale so the build flags them.
        return (
            f'<a class="ref ref-stale" href="#{ref_id}" '
            f'title="Unresolved reference: {ref_id}">{match.group("fallback")}?</a>'
        )

    return _REF_RE.sub(resolve_ref, out)


_ATTR = {"&": "&amp;", "<": "&lt;", '"': "&quot;"}
_TEXT = {"&": "&amp;", "<": "&lt;", ">": "&gt;"}


def _attr(s: str) -> str:
    return "".join(_ATTR.get(c, c) for c in s)


def _text(s: str) -> str:
    return "".join(_TEXT.get(c, c) for c in s)
