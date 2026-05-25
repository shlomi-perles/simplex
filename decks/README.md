# decks/

Author content lives here, one directory per deck.

Each deck contains:
- `deck.toml` -- DeckConfig fields (slug, title, summary, tags, theme, scenes, quality)
- `slides.py` -- vanilla Manim subclassing `simplex.slides.*`
- `notes.md` -- academic-style notes (KaTeX math, `^[sidenotes]`,
  `[slide:N]` jump links, `\cite{key}` citations)
- `refs.bib` -- optional BibTeX bibliography; cited entries appear as
  alpha-style `[Auth23]` tags + an auto-rendered References section
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
  - `engine.text`: `Caption`, `TexPage` (fixed-width minipage), `color_tex`
  - `engine.code`: `code_block` + `highlight_code_lines` + `code_explain` + `transform_code_lines`
  - `engine.geometry`: convex hull + surrounding rectangle
  - `engine.region`: direction anchors + `shrink` + `reset` + `split_regions(axis, k)`
  - `engine.animations`: `set_exit_animation` + `register_exit` + `clear_scene(exclude=...)`
  - `engine.scaling`: `scale_to_fit(len_x, len_y, buff)`
  - `mobjects.graph` / `mobjects.array`: `Node`, `Edge`, `ArrayMob`, `ArrayPointer`
