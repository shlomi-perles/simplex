# manager/

Local browser manager for Simplex lecture repos.

## Public surface

- `serve` -- starts the HTTP server and opens the manager UI.
- `server.py` -- small stdlib HTTP API serving state, edits, jobs, and static
  assets.
- `state.py` -- deck discovery, scene scanning, Manim quality/cache option
  helpers, entrypoint editing, and deck defaults TOML editing.
- `jobs.py` -- background render/build jobs, stop/open controls, ANSI log
  capture, and output target lookup.
- `run_cli.py` -- isolated CLI subprocess entry point for manager jobs.
- `run_manim.py` -- Manim CLI wrapper that forces ANSI-rich console output for
  browser log rendering.
- `static/` -- compact HTML/CSS/JS manager client.

## Conventions

- Keep deck entrypoints as the current string list convention:
  `["slides.intro:Intro", "slides.surface:Surface@opengl"]`.
- Do not introduce structured entrypoint TOML. Reorder, remove, and add-back
  operations rewrite only the `entrypoints` string list.
- Use Manim's own `QUALITIES` constants for quality choices.
- Cache on is represented by no Manim flag; cache off is
  `--disable_caching`; explicit flush is `--flush_cache`.
- Scene open-after-render opens the rendered file chosen from Simplex output,
  including OpenGL scenes.

## Don't

- Don't persist jobs outside the current manager server process.
- Don't shell out through the public CLI module directly from a process that
  already imported it; use `simplex.manager.run_cli`.
- Don't make manager-only TOML schema changes. Decks must stay readable and
  editable by hand.
