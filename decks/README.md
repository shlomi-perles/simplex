# decks/

Author content lives here, one directory per deck.

Each deck contains:
- `deck.toml` -- DeckConfig fields (slug, title, summary, tags, theme, scenes, quality)
- `slides.py` -- vanilla Manim subclassing `simplex.slides.*`
- `notes.md` -- English notes rendered into the portal with KaTeX-ready math
- `assets/` -- optional images / data

Scaffold a new deck with:

```bash
uv run simplex new my-slug
```

Directories whose name starts with `_` (e.g. `_template/`) are skipped by `discover()`.
