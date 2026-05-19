# Simplex showcase

This deck is the canonical reference for every helper Simplex adds on top of
vanilla Manim. Each scene targets one module; read alongside the matching
`README.md` in `src/simplex/`.

## What's exercised

| Scene | Module | Helpers |
|-------|--------|---------|
| `TextHelpers` | `engine.text` | `Tex` body defaults, `Caption`, `TexPage` (default 20 cm + `width_cm` kwarg), `color_tex` |
| `CodeHelpers` | `engine.code` | `code_block`, `highlight_code_lines`, `code_explain`, `transform_code_lines` |
| `CodeWithMath` | `engine.code` | `code_with_math` -- inline LaTeX (`$...$`) in pseudocode, with `bold_math` + `math_color` styling |
| `GraphAndArray` | `mobjects.graph` + `mobjects.array` | `Node`, `Edge`, `ArrayMob`, `ArrayPointer` |
| `RegionAnchors` | `engine.region` | direction anchors (`UL`/`UR`/`DL`/`DR`/`ORIGIN`), `shrink`, `reset`, `split(axis, k)` |
| `ExitAnimations` | `engine.animations` | `set_exit_animation`, `register_exit`, `clear_scene(exclude=...)` |
| `GeometryHelpers` | `engine.geometry` | `get_convex_hull_polygon`, `get_surrounding_rectangle` |
| `GlyphMapTransform` | `engine.glyph_map` | `TransformByGlyphMap` -- explicit glyph-index morph |
| `TrackingHelpers` | `engine.dynamics` + `engine.geometry` | `VT` (`~`/`@`), `DN`, `Vcis` |
| `ShapeAndDebug` | `engine.geometry` + `engine.debug` + `engine.ghost_fade` | `SurroundingRectangleUnion`, `indexx_labels`, `bounding_box`, `GhostSlideFade` |
| `ScalingHelpers` | `engine.scaling` | `scale_to_fit(len_x, len_y, buff)`; demonstrates `Region.split` alongside |

## Notes

- The convex-hull demo requires SciPy. Install it via `pip install simplex-py[geometry]`; without it, the scene shows a caption pointing readers to the extras.
- `code_block` registers the Darcula Pygments style on first use; subsequent calls are a no-op.
- `code_with_math(src, ...)` replaces every `$...$` region in `src` with a `MathTex` glyph scaled to the surrounding code font (calibrated against a cached `Mq` reference, so `\infty` and `\bigcup_{i=1}^n` both land at the right size). Lines reflow so the rendered math width drives the layout, and the background is refit only when at least one substitution happens. Pass `bold_math=True` to wrap each match in `\boldsymbol{...}` and `math_color="..."` to recolour the math.
- `TexPage` is the encapsulated fixed-width helper (was `Definition`). Its default page width is **20 cm**; pass `width_cm=10.5` per call, or set the class attribute on a subclass (`class WidePage(TexPage): width_cm = 12.0`) for a deck-wide variant. The `{minipage}{<width>cm}` literal only appears inside `TexPage` itself -- themes no longer carry it.
- Body-sized prose uses plain `manim.Tex`. The plugin's `apply_theme_defaults` sets the body `font_size` and `color` so `Tex(...)` already matches what the old `BodyText` produced.
- `region.place(mob, anchor, buff=...)` accepts a Manim direction vector (`UP`, `DR`, `ORIGIN`, ...) -- string anchors raise `ValueError`.
- `region.split(axis, k)` returns `k` sub-regions strung along `axis` (e.g. `RIGHT` → left-to-right). Each piece keeps the perpendicular extent and gets `1/k` of the axis extent; their union is the original.
- Slide numbering and the wall clock live in the RevealJS host (toggle via `[web] show_slide_number` / `show_clock` in `deck.toml`). They are not drawn into each frame, so toggling them does not invalidate the manim cache.
- The MF-Tools-derived helpers deliberately drop everything Manim 0.20.x already ships -- `ValueTracker` arithmetic operators, `index_labels`, `ConvexHull`, `Polygon.round_corners`, `Union`, `BraceLabel`/`BraceText`, and `Mobject.always` all stay native. We only add what isn't already there.
- `TransformByGlyphMap` falls back to a `show_indices` mode if the leftover glyph counts don't line up -- pass an empty `glyph_map` (or `show_indices=True`) to see the index labels and write the right map.
- `VT` only adds `~vt`, `vt @ x`, `vt @= x`. The `+`, `-`, `*`, `/`, `**` operators are inherited from `ValueTracker` (added in Manim 0.19.1).
- `DN(callable_or_VT, ...)` attaches an `add_updater`, NOT `Mobject.always` -- the latter would snapshot the value once at attach time (a documented Manim gotcha).
- The auto-promoted `next_slide()` name (when the first call is bare) splits PascalCase boundaries (`DFSLecture` → `"DFS Lecture"`).

## Math sample

Inline: $\sum_{k=1}^n k = \tfrac{n(n+1)}{2}$.

Display:

$$
\int_{-\infty}^{\infty} e^{-x^2}\,dx = \sqrt{\pi}
$$

## Code sample

```python
def bfs(graph, start):
    queue = [start]
    visited = {start}
    while queue:
        node = queue.pop(0)
        for nb in graph[node]:
            if nb not in visited:
                visited.add(nb)
                queue.append(nb)
    return visited
```
