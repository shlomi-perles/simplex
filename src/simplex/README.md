# src/simplex

The Simplex package: manim plugin, theme tokens, slide bases, deck discovery,
render pipeline, web portal, and CLI.

## Public surface

- `simplex.plugin:activate` -- the `manim.plugins` entry-point (set `plugins = simplex` in your `manim.cfg`)
- `simplex.slides` -- `BaseSlide`, `make_chrome`
- `simplex.theme` -- `Theme`, `WebPalette`, `active_theme`, `get_active_theme`, `presets`, `render_web_css`
- `simplex.engine` -- `apply_theme_defaults`, `Region`, `Remove`, `register_exit`, `set_exit_animation`, `clear_scene`, `SimplexSectionType`
- `simplex.deck` -- `DeckConfig`, `discover`, `scaffold`
- `simplex.cli.commands:app` -- the Typer app behind `uv run simplex`

## Don't

- Don't import `manim_editor`. The legacy package is deprecated and not a dependency.
- Don't wrap Manim constructors. Authors write vanilla Manim; the framework configures defaults underneath via `Mobject.set_default(...)`.
- Don't add a custom quality enum. Use `manim.constants.QUALITIES` keys directly.
- Don't bypass the plugin entry-point by setting `manim.config` from your scene. The plugin runs once at import time; that's the correct seam.
