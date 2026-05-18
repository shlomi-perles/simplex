# engine/

Small additive helpers that augment vanilla Manim. **Never wrap Manim's constructors.**

## Public surface

- `apply_theme_defaults(theme)` -- calls `Mobject.set_default(...)` for Tex / MathTex / Text / Line / Dot / Arrow / Rectangle / Square (invoked by `simplex.plugin:activate`)
- `Region` -- mutable rectangular drawing area; default lives on `BaseSlide.region`
- `Remove(mob, **kw)` -- exit animation lookup; dispatches through `exit_for(mob)`
- `exit_for(mob)` -- resolves per-instance override -> MRO match in `DEFAULT_EXITS` -> `FadeOut`
- `register_exit(mob_type, factory)` -- register a default exit for a Mobject class
- `set_exit_animation(mob, factory)` -- per-instance exit override
- `clear_scene(scene, *, exclude=())` -- free function used by `BaseSlide.clear_scene`
- `SimplexSectionType` -- enum encoded into manim's native section JSON for the main/sub hierarchy

## Submodules (import directly to keep `simplex.engine` cheap)

- `engine.text` -- `BodyText`, `Caption`, `Definition`; `color_tex(eq, t2c)`; `search_shape_in_text`
- `engine.code` -- `code_block`, `highlight_code_lines`, `code_explain`, `transform_code_lines`; `DarculaStyle`, `register_darcula`
- `engine.geometry` -- `get_convex_hull_polygon`, `get_surrounding_rectangle`, `get_frame_center`, `Vcis`, `Arc3d`, `SurroundingRectangleUnion`
- `engine.transforms` -- `TransformByGlyphMap` (glyph-indexed Tex transitions), `GhostSlideFade`
- `engine.dynamics` -- `VT` (`~`/`@`/`@=` over `ValueTracker`), `DN` (auto-tracking `DecimalNumber`), `keep_orientation`, `maintain_apparent_stroke_width`
- `engine.scaling` -- `scale_to_fit` (multi-axis fit + buff), `scale_to_fit_mobject`, `scale_with_stroke_width`
- `engine.debug` -- `bounding_box`, `indexx_labels` (multi-color), `debug_glyph(s)`

## Don't

- Don't call `Mobject.set_default(...)` outside `apply_theme_defaults`.
- Don't subclass Manim Mobjects to inject defaults; use `set_default` via `apply_theme_defaults`.
- Don't reimplement what manim ships: `ValueTracker` arithmetic ops, `index_labels`, `ConvexHull`, `Union`, `Polygon.round_corners`, `scale_to_fit_height/_width/_depth`, `BraceLabel`/`BraceText`, `Mobject.always` -- all already in 0.20.x.
- Don't import manim at module load time from animations/section_types/region/defaults -- import inside the function so importing `simplex.engine` stays cheap.
