# web/static/

Vendored runtime assets: Tailwind CSS build, KaTeX, htmx. Copied verbatim to `site/static/` at build time.

## Don't

- Don't edit. Replace by upgrading the vendored version and committing the new file.
- Don't load these via CDN -- vendoring keeps the published Pages site offline-safe and avoids supply-chain risk.

Files are not committed in the initial scaffold: a follow-up commit vendors `tailwind.min.css`, the `katex/` directory, and `htmx.min.js` from their official releases.
