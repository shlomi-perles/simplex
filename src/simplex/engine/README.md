# engine/

Small additive helpers that augment vanilla Manim. **Never wrap Manim's constructors.**

## Public surface

- `configure_manim(theme, quality_key, media_dir=None)` -- mutates `manim.config` once per render
- `apply_theme_defaults(theme)` -- calls `Mobject.set_default(...)` for Tex / MathTex / Text / Line / Dot / Arrow / Rectangle
- `Region` -- mutable rectangular drawing area; default lives on `BaseSlide.region`
- `Remove(mob, **kw)` -- exit animation lookup via `mob._simplex_exit`; falls back to `FadeOut`
- `set_exit_animation(mob, anim_cls)` -- attach a custom exit on any Mobject

## Don't

- Don't call `Mobject.set_default(...)` from anywhere else -- it must live in `apply_theme_defaults`.
- Don't subclass Manim Mobjects to inject defaults; use `set_default` via `apply_theme_defaults`.
- Don't import manim at module load time; do it inside functions so importing `simplex.engine` stays cheap.
