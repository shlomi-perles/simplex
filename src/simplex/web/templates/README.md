# web/templates/

Jinja2 templates.

## Files

- `base.html` -- chrome (skip-link, header/nav, GA snippet, footer).
- `index.html` -- home page: one carousel per section.
- `_carousel.html` -- partial used by the home page.
- `section.html` -- "view all" grid for one section.
- `deck.html` -- timeline media player + sidebar + controls + notes.

## Don't

- Don't hand-edit generated HTML under `site/`. Re-render via `simplex build`.
- Don't put logic in templates -- compute it in `builder.py` and pass it in.
- Don't reference external CDNs. All assets are vendored under `static/`.
