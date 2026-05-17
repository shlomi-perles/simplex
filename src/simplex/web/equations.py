r"""Display-equation tags + cross-references.

Authors write standard LaTeX ``\tag{X}`` inside ``$$...$$`` (or already-
rewritten ``\[...\]``). We pull the tag out of the math content server-side
and emit a layout we control:

    <div class="equation" id="eq-X">
      <div class="math block">\[ ...math without \tag... \]</div>
      <span class="eq-tag">(X)</span>
    </div>

Why move the tag out of the math:

1. ``\ref{eq-X}`` cross-references need a stable anchor on a DOM element
   that doesn't get re-rendered by KaTeX.
2. KaTeX positions its built-in ``\tag`` absolutely at ``right: 0`` of
   the math element. When ``notes.js`` scales a wide equation to fit
   the column, the absolute tag rides inside the scaled box and ends
   up overlapping the formula. A grid-laid sibling stays at natural
   size, in its own column.

The returned `labels` map (``"eq-3" -> "(3)"``) is consumed by
``callouts.transform`` so ``\ref{eq-3}`` resolves to the linked
display text.
"""

import re

# Match a `<div class="math block">\[...\]</div>` produced by dollarmath +
# the renderer in `notes.py`.
_BLOCK_RE = re.compile(
    r'<div class="math block">\s*\\\[(?P<math>.*?)\\\]\s*</div>',
    re.DOTALL,
)
_TAG_RE = re.compile(r"\\tag\{(?P<label>[^}]+)\}")
_SLUG_RE = re.compile(r"[^a-z0-9]+")

_ESCAPE = {"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;"}


def _escape(s: str) -> str:
    return "".join(_ESCAPE.get(c, c) for c in s)


def transform(html: str) -> tuple[str, dict[str, str]]:
    """Extract ``\\tag{}`` from each display math block.

    Returns ``(rewritten_html, labels)`` where ``labels`` maps each
    ``eq-<slug>`` to its display string ``"(<original tag>)"``.
    """
    labels: dict[str, str] = {}
    # Track slug collisions: two equations both tagged `\tag{3}` get
    # `eq-3` and `eq-3-2`. Stable across a single build.
    used_slugs: dict[str, int] = {}

    def replace(match: re.Match[str]) -> str:
        math = match.group("math")
        tag_match = _TAG_RE.search(math)
        if not tag_match:
            return match.group(0)
        label = tag_match.group("label").strip()
        slug_base = _SLUG_RE.sub("-", label.lower()).strip("-") or "tag"
        count = used_slugs.get(slug_base, 0) + 1
        used_slugs[slug_base] = count
        slug = slug_base if count == 1 else f"{slug_base}-{count}"
        eq_id = f"eq-{slug}"
        display = f"({label})"
        labels[eq_id] = display

        clean_math = _TAG_RE.sub("", math).rstrip()
        return (
            f'<div class="equation" id="{_escape(eq_id)}">'
            f'<div class="math block">\\[{clean_math}\\]</div>'
            f'<span class="eq-tag">{_escape(display)}</span>'
            f"</div>"
        )

    new_html = _BLOCK_RE.sub(replace, html)
    return new_html, labels
