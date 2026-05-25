# mobjects/

Re-usable Simplex mobjects. Mirrors Manim's own `manim.mobject.*`
namespace convention.

## Public surface

- `Node` -- filled circle with centered `MathTex` label; registers a
  `ShrinkToCenter` exit animation.
- `Edge` -- `Line` between two anchors with optional `MathTex` weight
  label at the midpoint.
- `ArrayEntry` -- one cell of an `ArrayMob` (frame + value + optional
  index label).
- `ArrayMob` -- named horizontal array with animation helpers (`at`,
  `indicate_at`, `push`, `pop`, `swap`).
- `ArrayPointer` -- arrow pointing at an entry, with `to_entry(new_i)`
  animation.
- `OutlineProgressBar` -- linspace-driven dot progress bar used by
  `simplex.slides.OutlineScene`.

## Conventions

- All mobjects pull colors / strokes / fonts from
  `simplex.theme.context.get_active_theme()` at construction time.
- All mobjects are vanilla `VMobject` subclasses; they work in any
  `Scene`, not just `BaseSlide`.
- Exit animations are registered via
  `simplex.engine.animations.set_exit_animation` (no monkey-patching).

## Don't

- Don't hard-code colors. Read from the theme.
- Don't subclass to inject defaults -- pass kwargs at construction.
