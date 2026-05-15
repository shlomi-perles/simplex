# decks/

Author content lives here, one directory per deck.

Each deck contains:
- `deck.toml` -- DeckConfig fields (slug, title, summary, tags, theme, scenes, quality)
- `slides.py` -- vanilla Manim subclassing `simplex.slides.*`
- `notes.md` -- English notes rendered into the portal with KaTeX-ready math
- `assets/` -- optional images / data

Scaffold a new deck with:

    uv run simplex new my-slug

Directories whose name starts with `_` (e.g. `_template/`) are skipped by `discover()`.

Force a re-render or re-render only a few scenes:

    uv run simplex render my-slug --force
    uv run simplex render my-slug --scene SceneA --scene SceneB

See `src/simplex/render/README.md` for the full cache + re-render semantics.

## Bundled decks

- `_template/` -- starter copied by `simplex new` (skipped by `discover()`).
- `showcase/` -- canonical demo of every Simplex-specific helper:
  - `engine.text`: `BodyText`, `Caption`, `Definition`, `color_tex`
  - `engine.code`: `code_block` + `highlight_code_lines` + `code_explain`
  - `engine.geometry`: convex hull + surrounding rectangle
  - `engine.region`: anchors + `shrink` + `reset`
  - `engine.animations`: `set_exit_animation` + `clear_scene(exclude=...)`
  - `slides.components`: `Node`, `Edge`, `ArrayMob`, `ArrayPointer`
