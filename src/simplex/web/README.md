# web/

Static-site generator: notes -> HTML, Jinja templates, per-deck page + portal index.

## Public surface

- `notes.render(notes_md_path)` -- markdown-it + dollarmath -> HTML
- `builder.build(decks_dir, site_dir, cache_dir)` -- discover -> render -> pdf -> notes -> write

## Don't

- Don't bundle JS. htmx + KaTeX are vendored under `static/`.
- Don't hand-edit any HTML under `site/`. Edit templates instead.
- Don't import jinja templates as Python modules. Loaded via `PackageLoader("simplex.web", "templates")`.
