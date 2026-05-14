# src/simplex

The Simplex package: theme tokens, slide bases, deck discovery, render pipeline,
web portal, and CLI.

## Public surface

- `simplex.slides` -- `BaseSlide`, `TitleSlide`, `SectionDivider`, `ContentSlide`
- `simplex.theme` -- `Theme`, `active_theme`, `get_active_theme`, `presets`
- `simplex.engine` -- `configure_manim`, `apply_theme_defaults`, `Region`, `Remove`, `set_exit_animation`
- `simplex.deck` -- `DeckConfig`, `discover`, `scaffold`
- `simplex.cli.commands:app` -- the Typer app behind `uv run simplex`

## Don't

- Don't import `manim_editor`. The legacy package is deprecated and not a dependency.
- Don't wrap Manim constructors. Authors write vanilla Manim; the framework configures defaults underneath via `Mobject.set_default(...)`.
- Don't add a custom quality enum. Use `manim.constants.QUALITIES` keys directly.
