# tests/engine/

Tests for `simplex.engine`: animations registry, Region geometry.

## Conventions

- `test_region.py` uses `pytest.importorskip("manim")` because `Region.full_frame()` reads `manim.config.frame_width`.
- `test_animations.py` exercises `Remove`'s lookup with a stub animation class so it can run without a Manim scene context.

## Don't

- Don't call `apply_theme_defaults` in tests -- it mutates global Manim state.
