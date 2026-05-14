# web/

Static-site generator: home carousels, deck pages, viewer bridge, notes
markdown.

## Public surface

- `SiteConfig.load()` -- merge committed `site.toml` with env overrides
  (`SIMPLEX_GA_TAG`, `SIMPLEX_BASE_URL`, `SIMPLEX_BRAND`, `SIMPLEX_PREVIEW`).
- `notes.render(notes_md_path, slide_count=...)` -- markdown-it +
  dollarmath + `[slide:N]` plugin -> HTML.
- `builder.build(decks_dir, site_dir, cache_dir, render=True)` -- discover
  -> render -> pdf -> notes -> emit per-deck `slides.html` + page +
  per-section pages + home.

## Don't

- Don't bundle JS or load CDNs. Tailwind / KaTeX / RevealJS / viewer.js are
  vendored under `static/` (see `static/README.md`).
- Don't hand-edit anything under `site/`. Edit templates / CSS instead.
- Don't import Jinja templates as Python modules. Loaded via
  `PackageLoader("simplex.web", "templates")`.
