# src/simplex

The `simplex` distribution's half of the namespace: deck discovery,
render pipeline, web portal, and CLI. The plugin half (`simplex.plugin`,
`simplex.engine`, `simplex.theme`, `simplex.slides`) is shipped by the
`manim-simplex` distribution and merged into this same namespace at
import time via PEP 420.

This directory ships **no** `__init__.py`. Don't add one -- it would
shadow the implicit namespace and break the `manim-simplex` half.

## Public surface (this distribution)

- `simplex.deck` -- `DeckConfig`, `discover`, `scaffold`
- `simplex.render` -- `runner`, `reconcile`, `html`, `pdf`, `pptx`, `thumbnail`
- `simplex.web` -- `builder`, `notes`, bibliography stack, templates, static, SSE reload
- `simplex.cli.commands:app` -- the Typer app behind `uv run simplex`

## Public surface (re-exported from `manim-simplex`)

- `simplex.plugin:activate` -- the `manim.plugins` entry-point (set `plugins = simplex` in your `manim.cfg`)
- `simplex.slides` -- `BaseSlide`, `make_chrome`
- `simplex.theme` -- `Theme`, `WebPalette`, `active_theme`, `get_active_theme`, `presets`, `render_web_css`
- `simplex.engine` -- `apply_theme_defaults`, `Region`, `Remove`, `register_exit`, `set_exit_animation`, `clear_scene`, `SimplexSectionType`

## Don't

- Don't add `src/simplex/__init__.py`. The namespace must stay implicit.
- Don't import `manim_editor`. The legacy package is deprecated and not a dependency.
- Don't wrap Manim constructors. Authors write vanilla Manim; the framework configures defaults underneath via `Mobject.set_default(...)`.
- Don't add a custom quality enum. Use `manim.constants.QUALITIES` keys directly.
- Don't bypass the plugin entry-point by setting `manim.config` from your scene. The plugin runs once at import time; that's the correct seam.
