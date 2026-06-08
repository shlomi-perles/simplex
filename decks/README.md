# decks/

Author-facing deck content lives here. This package repo keeps only the
showcase deck, but downstream lecture repos use the same layout.

Each deck contains:

- `deck.toml`: deck metadata, ordered `entrypoints`, optional publication
  `date`, slide-theme overrides, and web-page options.
- `slides/`: Manim scene modules using `simplex.Slide` or
  `simplex.ThreeDSlide`.
- `notes.md`: academic-style notes with KaTeX math, `^[sidenotes]`,
  `[slide:key-idea]` jump links, `\cite{key}` citations, theorem callouts, and
  generated references.
- `refs.bib`: optional BibTeX bibliography.
- `assets/`: optional images, data, or other deck-local files.
- `manim.cfg`: optional. Prefer the project-root `manim.cfg`; use a deck-local
  file only for overrides. Simplex merges the two before rendering.

Scaffold a new deck with:

```bash
uv run simplex new my-slug
```

Direct one scene to ManimCE's OpenGL renderer by suffixing its entrypoint:

```toml
entrypoints = ["slides.intro:Intro", "slides.surface:SurfaceColoring@opengl"]
```

Deck dates shown on homepage cards resolve in this order:

1. Explicit `date = "YYYY-MM-DD"` in `deck.toml`.
2. First Git commit that added the deck.
3. Last slide-structure change in `deck.toml`.
4. Last changed Python file in the deck.

Set `[web] show_notes_date = true` to show the resolved date under the first
notes heading and in the notes PDF.

Slide note anchors are automatic. A visible slide title `Key Idea` is
referenced as `[slide:key-idea]`; do not add manual note anchors to
`deck.toml`.

Directories whose name starts with `_` are skipped by `discover()`.

Force a re-render or re-render only a few scenes:

```bash
uv run simplex render my-slug --disable_caching
uv run simplex render my-slug --scene SceneA --scene SceneB
```

See `src/simplex/render/README.md` for render subprocess and cache semantics.

## Bundled Decks

- `showcase/`: canonical demo of Simplex-specific helpers.

The bundled scaffold template lives in `src/simplex/deck/_template/` so it can
ship inside the `manim-simplex` package.
