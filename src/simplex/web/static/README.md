# web/static/

Vendored runtime assets, copied verbatim to `site/static/` at build time.

## Committed

- `simplex.css` -- site-specific styles (carousel, deck page, slide-refs).
- `viewer.js` -- parent-page bridge for the deck iframe + carousel arrows.

## Vendored at install time (not committed)

- `tailwind.js` (Tailwind Play CDN -- JIT runtime, required for arbitrary-value classes)
- `katex/` (CSS + fonts + JS auto-render)
- `reveal.js/` (`reveal.js`, `reveal.css`, `reset.css`, `theme/simplex.css`)
- `htmx.min.js` (optional, kept for future progressive enhancement)

## Don't

- Don't load these via CDN -- vendoring keeps Pages offline-safe.
- Don't edit the vendored files; upgrade them with `scripts/vendor.sh`.
