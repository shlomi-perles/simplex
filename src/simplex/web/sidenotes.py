"""Tufte-style sidenotes via `mdit-py-plugins`'s ``footnote_plugin``.

Authors write ``^[some marginal aside]`` inline. Internally markdown-it emits
the standard footnote markup (`<sup class="footnote-ref">` + a
``<section class="footnotes">`` at the bottom). We post-process that HTML so
each footnote body floats next to its anchor as a Tufte-style sidenote:

    text<sup class="sidenote-ref" id="snref-1">1</sup><aside
        class="sidenote" id="sn-1" role="note">body</aside> more text.

The bottom ``<section class="footnotes">`` is removed so wide-screen readers
see only the marginal note; narrow screens collapse the sidenote inline (via
CSS in ``static/simplex.css``).

Pure HTML transformation -- no JS, no token-tree gymnastics. This keeps the
markdown-it plugin chain (footnotes + dollarmath + citations + slide-ref)
working without conflicts.
"""

import re

# Matches one <li id="fnN" ...>...</li>, capturing the id and the inner HTML
# (greedy enough to span nested tags, lazy enough to stop at the next list
# item). We rely on the footnote plugin's stable shape.
_LI_RE = re.compile(
    r'<li\s+id="fn(?P<n>\d+)"[^>]*>\s*(?P<body>.*?)\s*</li>',
    re.DOTALL,
)
_REF_RE = re.compile(
    r'<sup\s+class="footnote-ref">\s*<a[^>]*href="#fn(?P<n>\d+)"[^>]*>\[(?P<num>\d+)\]</a>\s*</sup>',
)
_BACKREF_RE = re.compile(r'\s*<a[^>]*class="footnote-backref"[^>]*>[^<]*</a>')
_SECTION_RE = re.compile(
    r'<hr\s+class="footnotes-sep"\s*/?>\s*<section\s+class="footnotes">.*?</section>',
    re.DOTALL,
)
_OUTER_P_RE = re.compile(r"^\s*<p>(.*)</p>\s*$", re.DOTALL)


def transform(html: str) -> str:
    """Rewrite footnote markup in ``html`` into Tufte sidenote markup."""
    bodies = _extract_bodies(html)
    if not bodies:
        return html
    html = _SECTION_RE.sub("", html)

    def replace_ref(match: re.Match[str]) -> str:
        n = match.group("n")
        num = match.group("num")
        body = bodies.get(n, "")
        return _render_sidenote(n, num, body)

    return _REF_RE.sub(replace_ref, html)


def _extract_bodies(html: str) -> dict[str, str]:
    bodies: dict[str, str] = {}
    for match in _LI_RE.finditer(html):
        n = match.group("n")
        body = _BACKREF_RE.sub("", match.group("body"))
        # Footnote bodies are wrapped in a <p>; for an inline sidenote we want
        # the inner content, not a block-level <p>.
        single_para = _OUTER_P_RE.match(body)
        if single_para:
            body = single_para.group(1)
        bodies[n] = body.strip()
    return bodies


def _render_sidenote(n: str, num: str, body: str) -> str:
    return (
        f'<label for="sn-toggle-{n}" class="sidenote-ref" id="snref-{n}">{num}</label>'
        f'<input type="checkbox" id="sn-toggle-{n}" class="sidenote-toggle" '
        'aria-hidden="true" />'
        f'<aside class="sidenote" id="sn-{n}" role="note">{body}</aside>'
    )
