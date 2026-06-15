# src/simplex

The `simplex` package is owned by the `manim-simplex` distribution.

It contains both halves of the product:

- `simplex.plugin` -- Manim plugin entry point (`plugins = simplex`).
- `simplex.engine`, `simplex.theme`, `simplex.mobjects`, `simplex.slides` --
  authoring helpers for Manim scenes and slide decks.
- `simplex.manifest` and `simplex.section` -- shared slide metadata schema.
- `simplex.deck` -- deck config, discovery, and scaffolding.
- `simplex.render` -- render orchestration, reconciliation, thumbnails, slide
  PDFs, notes PDF, and HTML export.
- `simplex.web` -- portal builder, notes renderer, templates, static assets,
  citations, refs, and live reload support.
- `simplex.cli.commands:app` -- the Typer app behind the `simplex` command.

## Package Boundary

Do not split this import root across multiple distributions. The top-level
`simplex.__init__` facade is intentionally lazy so authoring imports stay
pleasant (`from simplex import Slide`) while CLI and web modules do not
eagerly import Manim.

## Don't

- Don't add a second PyPI distribution that also writes into `simplex.*`.
- Don't import `manim_editor`; the legacy package is deprecated and not a
  dependency.
- Don't wrap Manim constructors. Authors write vanilla Manim; the framework
  configures defaults underneath via `Mobject.set_default(...)`.
- Don't import Manim from CLI/web parent paths just to interpret render
  settings. Keep defaults in project/deck `manim.cfg` files and pass one-off
  overrides through Manim's own CLI parser.
- Don't bypass the plugin entry point by setting `manim.config` from scenes.
  The plugin runs once at import time; that is the correct integration point.
