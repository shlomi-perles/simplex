# src/simplex

The `simplex` package is owned by the `manim-simplex` distribution.

It contains both halves of the product:

- `simplex.plugin` -- Manim plugin entry point (`plugins = simplex`).
- `simplex.engine`, `simplex.theme`, `simplex.mobjects`, `simplex.slides` --
  authoring helpers for Manim scenes and slide decks.
- `simplex.manifest` and `simplex.section` -- shared slide metadata schema.
- `simplex.deck` -- deck config, discovery, and scaffolding.
- `simplex.render` -- render orchestration, reconciliation, thumbnails, PDF,
  PPTX, and HTML export.
- `simplex.web` -- portal builder, notes renderer, templates, static assets,
  citations, refs, and live reload support.
- `simplex.cli.commands:app` -- the Typer app behind the `simplex` command.

## Package Boundary

Do not split this import root across multiple distributions. The top-level
`simplex.__init__` facade is intentionally lazy so authoring imports stay
pleasant (`from simplex import BaseSlide`) while CLI and web modules do not
eagerly import Manim.

## Don't

- Don't add a second PyPI distribution that also writes into `simplex.*`.
- Don't import `manim_editor`; the legacy package is deprecated and not a
  dependency.
- Don't wrap Manim constructors. Authors write vanilla Manim; the framework
  configures defaults underneath via `Mobject.set_default(...)`.
- Don't add a custom quality enum. Use `manim.constants.QUALITIES` keys
  directly.
- Don't bypass the plugin entry point by setting `manim.config` from scenes.
  The plugin runs once at import time; that is the correct integration point.
