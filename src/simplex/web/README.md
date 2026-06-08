# web/

Static-site generator: home carousels, deck pages, viewer bridge, academic
notes pipeline (markdown + math + citations + Tufte sidenotes).

## Public surface

- `SiteConfig.load()` -- merge committed `site.toml` with env overrides
  (`SIMPLEX_GA_TAG`, `SIMPLEX_BASE_URL`, `SIMPLEX_BRAND`, `SIMPLEX_PREVIEW`).
- `notes.render(notes_md_path, slide_count=..., slide_refs=...,
  bibliography=...)` -- markdown-it + dollarmath + footnotes +
  `[slide:label]` + `\cite{}` +
  `\ref{}` / `\autoref{}` -> Tufte-style academic HTML (serif body, Lato headings,
  right-margin sidenotes, colour-coded theorem callouts, references
  appendix, auto-fitted display math).
- `bibliography.Bibliography.load(refs_bib)` -- parse a `.bib`, assign
  biblatex `alpha` labels (`[DHS11]`-style), render the cited subset.
- `callouts.transform(html)` -- rewrite `> **Theorem.** \label{thm:first} ...`
  blockquotes as auto-numbered anchored `<aside class="callout callout-theorem"
  id="thm:first">` blocks; resolve `\ref{}` / `\autoref{}` placeholders to
  the display label.
- `builder.build(decks_dir, site_dir, *, render=True, site_cfg=None, only=(), scenes=(), watch=False)`
  -- discover -> render scene units -> compose/package timelines -> generate
  cue assets and exports -> notes -> emit per-deck page, manifest,
  per-section pages, and home.

## Notes and dates

- Slide labels are generated from visible slide titles. A slide named
  `Key Idea` is linked from notes with `[slide:key-idea]`.
- Homepage card dates use explicit `date` from `deck.toml`, then Git history,
  then filesystem fallbacks. `[web] show_notes_date = true` injects the same
  resolved date below the first notes heading.
- Bibliographies render as unbulleted lists with explicit alpha markers, for
  example `[KB15]`.

## Don't

- Don't bundle JS or load CDNs. Tailwind / KaTeX / Shaka Player / Lato /
  Merriweather are vendored under `static/` (see `static/README.md`).
- Don't hand-edit anything under `site/`. Edit templates / CSS instead.
- Don't import Jinja templates as Python modules. Loaded via
  `PackageLoader("simplex.web", "templates")`.
- Don't write a manual "References" section in `notes.md`. Use
  `\cite{key}` and ship a `refs.bib`; the renderer appends the list.
