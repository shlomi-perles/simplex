# web/static/

Vendored runtime assets, copied verbatim to `site/static/` at build time.

## Committed

- `simplex.css` -- site-specific styles (carousel, deck page, academic
  notes typography, Tufte sidenotes, citations, bibliography).
- `tailwind.input.css` -- Tailwind v4 source (CSS-first config + `@source`
  globs). Compiled to `tailwind.css` by `simplex.web.vendor`.
- `viewer.js`, `notes.js` -- parent-owned timeline player, carousel arrows,
  and notes helpers.

## Vendored for builds (generated before release, ignored in git)

- `tailwind.css` (compiled from `tailwind.input.css` by the Tailwind v4
  standalone CLI; binary cached per-user, CSS shipped in the wheel)
- `katex/` (CSS + fonts + JS + auto-render)
- `shaka/` (compiled Shaka Player for HLS/CMAF playback)
- `htmx.min.js` (optional, kept for future progressive enhancement)
- `fonts/lato/` -- Lato 400/700/900 + italics (UI + headings)
- `fonts/merriweather/` -- Merriweather 400/700/900 + italics (body notes)

## Don't

- Don't load these via CDN -- vendoring keeps Pages offline-safe.
- Don't edit the vendored files; bump pinned versions in
  `simplex/web/vendor.py` and let the next build refetch.
