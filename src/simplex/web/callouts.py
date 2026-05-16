r"""Theorem-environment callouts + ``\ref{}`` resolution.

Rewrites ``<blockquote><p><strong>Theorem 3.1.</strong>...</p></blockquote>``
shapes into colour-coded, anchorable ``<aside>`` blocks:

    <aside class="callout callout-theorem" id="theorem-3-1">
      <span class="callout-tag">Theorem 3.1.</span> Let f...
    </aside>

Recognised types (case-insensitive): **theorem, lemma, proposition,
corollary, claim, fact, definition, example, remark, proof, observation,
note**. Anything else stays a normal blockquote.

Also resolves the placeholders emitted by `web/refs.py`:

    <a class="ref" data-simplex-ref="theorem-3-1" href="#theorem-3-1">
      theorem-3-1
    </a>
        |
        v
    <a class="ref" href="#theorem-3-1">Theorem 3.1</a>

Unknown ref ids get the ``ref-stale`` class (same convention as
``cite-stale`` / ``slide-ref-stale``).

Pure HTML transformation -- the markdown-it pipeline stays untouched.
"""

import re
from collections import defaultdict

# Types we colour-code. Order matters only for matching priority -- longer
# names first so "Proposition" beats a hypothetical "Prop" prefix.
_TYPES: tuple[str, ...] = (
    "Proposition",
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

# Match a leading `<p><strong>Theorem 3.1.</strong>` inside a blockquote.
# The number is optional (``Proof.`` / ``Remark.`` may stand alone). We
# capture the trailing period(s) too so the tag prints faithfully.
_TAG_RE = re.compile(
    rf"<p>\s*<strong>\s*(?P<type>{_TYPE_ALT})"
    r"(?:\s+(?P<num>\d+(?:\.\d+)*))?\s*\.\s*</strong>\s*",
    re.IGNORECASE,
)
_BLOCKQUOTE_RE = re.compile(r"<blockquote>(?P<body>.*?)</blockquote>", re.DOTALL)
_REF_RE = re.compile(
    r'<a class="ref" data-simplex-ref="(?P<id>[^"]+)" '
    r'href="#(?P=id)">(?P<fallback>[^<]+)</a>'
)


def transform(html: str) -> str:
    """Rewrite theorem-style blockquotes and resolve `\\ref{}` placeholders.

    Two-pass:
      1. Walk every blockquote, detect callout type, rewrite to `<aside>`,
         and record the label map (`"theorem-3-1" -> "Theorem 3.1"`).
      2. Walk every `<a class="ref">` placeholder and substitute the
         display label.
    """
    labels: dict[str, str] = {}
    # Auto-numbering for unnumbered callouts of the same type (e.g. multiple
    # standalone "Proof." blocks). Keyed by lowercase type.
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
        else:
            counters[kind] += 1
            slug_num = str(counters[kind])
            display = tag_match.group("type").title()

        block_id = f"{kind}-{slug_num}"
        # Record both the bare id and the numbered display so refs work.
        labels[block_id] = display

        tag_html = f'<span class="callout-tag">{display}.</span> '
        new_body = body[: tag_match.start()] + "<p>" + tag_html + body[tag_match.end() :]
        return (
            f'<aside class="callout callout-{kind}" id="{block_id}" role="note">{new_body}</aside>'
        )

    out = _BLOCKQUOTE_RE.sub(rewrite_blockquote, html)

    def resolve_ref(match: re.Match[str]) -> str:
        ref_id = match.group("id")
        if ref_id in labels:
            return f'<a class="ref" href="#{ref_id}">{labels[ref_id]}</a>'
        # Slide refs / external IDs may legitimately not be in the label
        # map; mark unresolved ones as stale so the build flags them.
        return (
            f'<a class="ref ref-stale" href="#{ref_id}" '
            f'title="Unresolved reference: {ref_id}">{match.group("fallback")}?</a>'
        )

    return _REF_RE.sub(resolve_ref, out)
