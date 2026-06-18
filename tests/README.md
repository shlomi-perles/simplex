# tests/

Pytest suites for the `manim-simplex` package.

## Layout

- `tests/test_section.py` -- `SimplexSectionType` enum behaviour. Pure
  Python.
- `tests/test_manifest.py` -- manifest schema v2, cue validation, theme media,
  JSON round-trip, helper methods. Pure Python.
- `tests/theme/` -- palette / preamble immutability, preset round-trips,
  context push/pop. Stdlib + pytest only.
- `tests/engine/` -- `Region` math, `ExitAnim` lookup (WeakKeyDictionary +
  thread-safe registry), `HighlightResult`, glyph_map / ghost_fade
  animations, geometry, dynamics, text, scaling, debug. Manim-touching
  cases use `pytest.importorskip("manim")`.
- `tests/mobjects/` -- smoke construction tests for `Node`, `Edge`, ...
- `tests/slides/` -- `SimplexScene` cue recording and `make_chrome` helpers.
- `tests/deck/` -- deck config, section config, discovery, and scaffolding.
- `tests/render/` -- runner command construction, timeline rebasing,
  packaging helpers, cue images, exports.
- `tests/manager/` -- deck manager TOML editing, scene discovery, Manim
  option forwarding, job naming, output opening, and ANSI wrapper behavior.
- `tests/web/` -- notes rendering, citations, equations, site config, portal
  builder, and browser-level generated player checks.
- `tests/cli/` -- Typer command surface and thin orchestration behavior.

## Don't

- Don't add full visual renders to unit tests. Render-smoke lives in CI via a
  temporary deck created with `simplex new`.
- Don't import `manim` in `conftest.py`; keep collection fast.
- Don't call `apply_theme_defaults` -- it mutates global Manim state.
- Don't add browser tests for static markup that a normal HTML assertion can
  cover; keep Playwright focused on media-player behavior, storage, and real
  DOM behavior.
