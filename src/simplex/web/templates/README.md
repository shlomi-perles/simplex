# web/templates/

Jinja2 templates: `base.html` (chrome), `index.html` (deck grid), `deck.html` (slides + notes + PDF).

## Don't

- Don't hand-edit generated HTML under `site/`. Re-render via `simplex build`.
- Don't put logic in templates -- compute it in `builder.py` and pass it in.
- Don't reference external CDNs. All assets are vendored under `static/`.
