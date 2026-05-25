# tests/engine/

Tests for `simplex.engine`: animations registry (WeakKeyDictionary +
thread-safe defaults), Region geometry, code helpers, glyph_map +
ghost_fade animations, dynamics, geometry, text, scaling, debug.

## Conventions

- `test_region.py` uses `pytest.importorskip("manim")` because
  `Region.full_frame()` reads `manim.config.frame_width`.
- `test_animations.py` exercises `Remove`'s lookup with a stub animation
  class so it can run without a Manim scene context.
- `test_glyph_map.py` exercises only the `_interpret_delay` rate-func
  shifter; full glyph-mapping behaviour needs a LaTeX render and lives
  in the CI render-smoke.

## Don't

- Don't call `apply_theme_defaults` in tests -- it mutates global Manim
  state.
- Don't depend on the manim-slides canvas in `test_animations.py`;
  `clear_scene`'s canvas path is exercised in `tests/slides/`.
