# web/static/

Vendored runtime assets, copied verbatim to `site/static/` at build time.

## Committed

- `simplex.css` -- site-specific styles (carousel, deck page, academic
  notes typography, Tufte sidenotes, citations, bibliography).
- `viewer.js` -- parent-page bridge for the deck iframe + carousel arrows.

## Vendored for builds (not committed)

- `tailwind.js` (Tailwind Play CDN -- JIT runtime, required for arbitrary-value classes)
- `katex/` (CSS + fonts + JS + auto-render)
- `reveal.js/` (`reveal.js`, `reveal.css`, `reset.css`)
- `htmx.min.js` (optional, kept for future progressive enhancement)
- `fonts/lato/` -- Lato 400/700/900 + italics (UI + headings)
- `fonts/merriweather/` -- Merriweather 400/700/900 + italics (body notes)

## Don't

- Don't load these via CDN -- vendoring keeps Pages offline-safe.
- Don't edit the vendored files; upgrade them with `scripts/vendor.sh`.
