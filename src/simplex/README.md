# src/simplex

The `simplex-web` distribution's half of the package: deck discovery,
render pipeline, web portal, and CLI. The plugin half (`simplex.plugin`,
`simplex.engine`, `simplex.theme`, `simplex.slides`) is shipped by the
`manim-simplex` distribution, whose top-level facade extends the package
path so these web modules compose with the authoring API.

This directory ships **no** runtime `__init__.py`. Don't add one -- the
runtime facade belongs to `manim-simplex`. The local `__init__.pyi` is
only a shallow typing stub for this repo's strict checks.

## Public surface (this distribution)

- `simplex.deck` -- `DeckConfig`, `discover`, `scaffold`
- `simplex.render` -- `runner`, `reconcile`, `html`, `pdf`, `pptx`, `notes_pdf`, `filenames`, `thumbnail`
- `simplex.web` -- `builder`, `notes`, bibliography stack, templates, static, SSE reload
- `simplex.cli.commands:app` -- the Typer app behind `uv run simplex`

## Public surface (re-exported from `manim-simplex`)

- `simplex.plugin:activate` -- the `manim.plugins` entry-point (set `plugins = simplex` in your `manim.cfg`)
- `simplex.slides` -- `BaseSlide`, `make_chrome`
- `simplex.theme` -- `Theme`, `WebPalette`, `active_theme`, `get_active_theme`, `presets`, `render_web_css`
- `simplex.engine` -- `apply_theme_defaults`, `Region`, `Remove`, `register_exit`, `set_exit_animation`, `clear_scene`, `SimplexSectionType`

## Don't

- Don't add `src/simplex/__init__.py`. The runtime facade belongs to `manim-simplex`.
- Don't import `manim_editor`. The legacy package is deprecated and not a dependency.
- Don't wrap Manim constructors. Authors write vanilla Manim; the framework configures defaults underneath via `Mobject.set_default(...)`.
- Don't add a custom quality enum. Use `manim.constants.QUALITIES` keys directly.
- Don't bypass the plugin entry-point by setting `manim.config` from your scene. The plugin runs once at import time; that's the correct seam.
