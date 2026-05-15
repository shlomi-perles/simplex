# engine/

Small additive helpers that augment vanilla Manim. **Never wrap Manim's constructors.**

## Public surface

- `configure_manim(theme, quality_key, media_dir=None)` -- mutates `manim.config` once per render
- `apply_theme_defaults(theme)` -- calls `Mobject.set_default(...)` for Tex / MathTex / Text / Line / Dot / Arrow / Rectangle / Square
- `Region` -- mutable rectangular drawing area; default lives on `BaseSlide.region`
- `Remove(mob, **kw)` -- exit animation lookup via `mob._simplex_exit`; falls back to `FadeOut`
- `set_exit_animation(mob, anim_cls)` -- attach a custom exit on any Mobject

## Submodules (import directly to keep `simplex.engine` cheap)

- `engine.text` -- `BodyText`, `Caption`, `Definition`; `color_tex(eq, t2c)`; `search_shape_in_text`
- `engine.code` -- `code_block`, `highlight_code_lines`, `code_explain`, `transform_code_lines`; `DarculaStyle`
- `engine.geometry` -- `get_convex_hull_polygon`, `get_surrounding_rectangle`, `get_frame_center`, `Vcis`, `Arc3d`, `SurroundingRectangleUnion`
- `engine.transforms` -- `TransformByGlyphMap` (glyph-indexed Tex transitions), `GhostSlideFade`
- `engine.dynamics` -- `VT` (`~`/`@`/`@=` over `ValueTracker`), `DN` (auto-tracking `DecimalNumber`), `keep_orientation`, `maintain_apparent_stroke_width`
- `engine.scaling` -- `scale_to_fit` (multi-axis fit + buff), `scale_to_fit_mobject`, `scale_with_stroke_width`
- `engine.debug` -- `bounding_box`, `indexx_labels` (multi-color), `debug_glyph(s)`

## Don't

- Don't call `Mobject.set_default(...)` outside `apply_theme_defaults`.
- Don't subclass Manim Mobjects to inject defaults; use `set_default` via `apply_theme_defaults`.
- Don't reimplement what manim ships: `ValueTracker` arithmetic ops, `index_labels`, `ConvexHull`, `Union`, `Polygon.round_corners`, `scale_to_fit_height/_width/_depth`, `BraceLabel`/`BraceText`, `Mobject.always` -- all already in 0.20.x.
- Don't import manim at module load time from animations/config/region/defaults -- import inside the function so importing `simplex.engine` stays cheap. The eager modules above import manim because that's their entire job.
