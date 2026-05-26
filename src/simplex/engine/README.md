# engine/

Small additive helpers that augment vanilla Manim. **Never wrap Manim's constructors.**

## Public surface

- `apply_theme_defaults(theme)` -- calls `Mobject.set_default(...)` for Tex / MathTex / Text / Line / Dot / Arrow / Rectangle / Square (invoked by `simplex.plugin:activate`)
- `Region` -- transparent Manim `Rectangle` subclass used as a mutable drawing area; default lives on `BaseSlide.region`
- `ExitAnim(mob, **kw)` -- exit animation lookup; dispatches through `exit_for(mob)` (named `ExitAnim` so it never collides with Manim's `Add` Animation pair)
- `exit_for(mob, **kw)` -- per-instance override (WeakKeyDictionary) -> MRO match in defaults -> `FadeOut`
- `register_exit(mob_type, factory)` -- register a default exit for a Mobject class
- `set_exit_animation(mob, factory)` -- per-instance exit override (stored in a `WeakKeyDictionary`; no monkey-patching)
- `clear_scene(scene, *, exclude=())` -- free function used by `BaseSlide.clear_scene`
- `HighlightResult` -- typed return for `highlight_code_lines` (fade + optional indicate, iterable)

Cross-package types live one level up:

- `simplex.section.SimplexSectionType` -- enum encoded into Manim's section JSON
- `simplex.manifest.DeckManifest` / `MainSlide` / `Subsection` -- web builder contract

## Submodules (import directly to keep `simplex.engine` cheap)

- `engine.text` -- `Caption`, `TexPage` (fixed-width minipage; `width_cm` kwarg / class attr); `color_tex(eq, t2c)`; `search_shape_in_text`. Body-sized paragraphs use plain `manim.Tex` -- `apply_theme_defaults` already sets `font_size=theme.typography.body`.
- `engine.code` -- `code_block`, `highlight_code_lines`, `code_explain`, `transform_code_lines`; `DarculaStyle`, `register_darcula`; `HighlightResult`
- `engine.geometry` -- `get_surrounding_rectangle` (rotated rect spanning two mobjects), `get_frame_center`, `Arc3d` (sphere arc; Manim's `ArcBetweenPoints` is 2D), `SurroundingRectangleUnion` (merged surrounding rect for groups). For convex hulls, call `manim.ConvexHull` directly; for unit vectors at an angle, use `manim.utils.space_ops.rotate_vector(RIGHT, theta)`; for normalising a vector, use `manim.utils.space_ops.normalize`.
- `engine.glyph_map` -- `TransformByGlyphMap` (glyph-indexed Tex transitions)
- `engine.ghost_fade` -- `GhostSlideFade` (one-shot fade-in/drift/fade-out cue)
- `engine.dynamics` -- `VT` (`~`/`@`/`@=` over `ValueTracker`), `DN` (auto-tracking `DecimalNumber`), `keep_orientation`, `maintain_apparent_stroke_width`
- `engine.scaling` -- `scale_to_fit` (multi-axis fit + buff), `scale_to_fit_mobject`, `scale_stroke_aware` (Manim's vanilla `scale` keeps stroke pixel-constant; this helper rescales stroke width across the family)
- `engine.debug` -- `bounding_box`, `indexx_labels` (multi-color), `debug_glyph(s)`

## Don't

- Don't call `Mobject.set_default(...)` outside `apply_theme_defaults`.
- Don't subclass Manim Mobjects to inject defaults; use `set_default` via `apply_theme_defaults`.
- Don't reimplement what Manim ships: `ValueTracker` arithmetic ops, `index_labels`, `ConvexHull` (with QuickHull) and `Polygon.round_corners`, `Union`, `manim.utils.space_ops.normalize` / `angle_of_vector` / `rotate_vector`, `manim.constants.QUALITIES` (`flag` field), `scale_to_fit_height/_width/_depth`, `BraceLabel`/`BraceText`, `Mobject.always` -- all already in 0.20.x.
- Don't reimplement Manim geometry in layout helpers. `Region` is a transparent `Rectangle`, so use native methods such as `get_critical_point`, `move_to(..., aligned_edge=...)`, and `get_center_of_mass` where they fit.
- Don't monkey-patch Mobjects (no `_simplex_*` attributes). Use the `WeakKeyDictionary` registry in `animations.py` instead.
