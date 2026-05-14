# engine/

Small additive helpers that augment vanilla Manim. **Never wrap Manim's constructors.**

## Public surface

- `configure_manim(theme, quality_key, media_dir=None)` -- mutates `manim.config` once per render
- `apply_theme_defaults(theme)` -- calls `Mobject.set_default(...)` for Tex / MathTex / Text / Line / Dot / Arrow / Rectangle / Square
- `Region` -- mutable rectangular drawing area; default lives on `BaseSlide.region`
- `Remove(mob, **kw)` -- exit animation lookup via `mob._simplex_exit`; falls back to `FadeOut`
- `set_exit_animation(mob, anim_cls)` -- attach a custom exit on any Mobject

## Submodules (import directly to keep `simplex.engine` cheap)

- `engine.text` -- `BodyText`, `Caption`, `Definition` (Tex subclasses); `color_tex(eq, t2c)`; `search_shape_in_text(text, shape)`
- `engine.code` -- `code_block(code, language=...)` wrapping `manim.Code`; `highlight_code_lines`, `code_explain`, `transform_code_lines`; `DarculaStyle` + `register_darcula()`
- `engine.geometry` -- `get_convex_hull_polygon(points)` (delegates to `manim.ConvexHull`), `get_surrounding_rectangle(a, b)`, `get_frame_center(...)`

## Don't

- Don't call `Mobject.set_default(...)` outside `apply_theme_defaults`.
- Don't subclass Manim Mobjects to inject defaults; use `set_default` via `apply_theme_defaults`.
- Don't import manim at module load time from animations/config/region/defaults -- import inside the function so importing `simplex.engine` stays cheap. `text`, `code`, `geometry` import manim eagerly because that's their entire job.
- Don't re-implement Dastimator's `compile_code_tex` here. `manim.Code` doesn't expose `code_json` / `tab_spaces`; LaTeX-in-code is out of scope until upstream offers a hook.
