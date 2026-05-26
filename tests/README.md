# tests/

Pytest suites for the `manim-simplex` package.

## Layout

- `tests/test_section.py` -- `SimplexSectionType` enum behaviour. Pure
  Python.
- `tests/test_manifest.py` -- `DeckManifest`, `MainSlide`, `Subsection`
  schema, JSON round-trip, helper methods. Pure Python.
- `tests/theme/` -- palette / preamble immutability, preset round-trips,
  context push/pop. Stdlib + pytest only.
- `tests/engine/` -- `Region` math, `ExitAnim` lookup (WeakKeyDictionary +
  thread-safe registry), `HighlightResult`, glyph_map / ghost_fade
  animations, geometry, dynamics, text, scaling, debug. Manim-touching
  cases use `pytest.importorskip("manim")`.
- `tests/mobjects/` -- smoke construction tests for `Node`, `Edge`, ...
- `tests/slides/` -- `BaseSlide.next_slide` section-type resolution
  (no auto-promotion, fail-loudly path) and `make_chrome` purity tests.
- `tests/deck/` -- deck config, section config, discovery, and scaffolding.
- `tests/render/` -- manifest reconciliation, HTML/PDF helpers, thumbnails,
  runner command construction.
- `tests/web/` -- notes rendering, citations, equations, site config, portal
  builder.
- `tests/cli/` -- Typer command surface and thin orchestration behavior.

## Don't

- Don't add full visual renders to unit tests -- the manim-slides subprocess is
  too slow. Render-smoke lives in CI via `simplex test --only showcase`.
- Don't import `manim` in `conftest.py`; keep collection fast.
- Don't call `apply_theme_defaults` -- it mutates global Manim state.
