# tests/

Pytest suite. One subdirectory per `src/simplex/` package mirroring the import path.

## Conventions

- Pure-Python tests live next to the module they target (`tests/theme/`, `tests/engine/`).
- Snapshot tests use `syrupy`. Commit `.ambr` files alongside the test.
- A smoke render of `decks/_template/` runs in CI.
- No conftest fixtures that pull in `manim` unless the test actually needs it (manim import is slow).
