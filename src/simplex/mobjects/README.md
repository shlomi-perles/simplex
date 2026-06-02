# mobjects/

Reusable Simplex mobjects. Mirrors Manim's own `manim.mobject.*`
namespace convention.

## Public surface

- `Node` -- filled circle with centered `MathTex` label; registers a
  `ShrinkToCenter` exit animation.
- `Edge` -- `Line` between two anchors with optional `MathTex` weight
  label at the midpoint.
- `ArrayCell` / `ArrayEntry` -- one array slot (frame + value + optional
  index label).
- `Array` / `ArrayMob` -- one-dimensional array with animation helpers
  (`animate_set_value`, `animate_append`, `animate_remove`, `animate_swap`).
- `ArrayPointer` -- arrow pointing at a cell, with `animate_to(new_i)`.
- `OutlineProgressBar` -- linspace-driven dot progress bar used by
  `simplex.slides.OutlineScene`.

## Conventions

- All mobjects pull colors / strokes / fonts from
  `simplex.theme.context.get_active_theme()` at construction time.
- All mobjects are vanilla `VMobject` subclasses; they work in any
  `Scene`, not just `Slide`.
- Exit animations are registered via
  `simplex.engine.animations.set_exit_animation` (no monkey-patching).

## Don't

- Don't hard-code colors. Read from the theme.
- Don't subclass to inject defaults -- pass kwargs at construction.
