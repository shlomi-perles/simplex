# Simplex showcase

This deck is the canonical reference for every helper Simplex adds on top of
vanilla Manim. Each scene targets one module; read alongside the matching
`README.md` in `src/simplex/`.

## What's exercised

| Scene | Module | Helpers |
|-------|--------|---------|
| `TextHelpers` | `engine.text` | `Tex` body defaults, `Caption`, `TexPage` (`page_width`, `buff`, `math_spacing`, `equation(n)`), `color_substrings` |
| `CodeHelpers` | `engine.code` | `code_block`, `highlight_code_lines`, `code_explain`, `transform_code_lines` |
| `CodeWithMath` | `engine.code` | `code_with_math` -- inline LaTeX (`$...$`) in pseudocode, with `bold_math` + `math_color` styling |
| `PseudocodeBlock` | `engine.code` | `pseudocode_block` -- algorithm2e LaTeX rendered as a `Code` object with numbered `code_lines` |
| `GraphAndArray` | `mobjects.graph` + `mobjects.array` | `Node`, `Edge`, `Array`, `ArrayPointer` |
| `RegionAnchors` | `engine.region` | direction anchors (`UL`/`UR`/`DL`/`DR`/`ORIGIN`), `shrink`, `reset`, `split_regions(axis, k)` |
| `ExitAnimations` | `engine.animations` | `set_exit_animation`, `register_exit`, `clear_scene(exclude=...)` |
| `GeometryHelpers` | `engine.geometry` | `get_surrounding_rectangle` (rotated rect spanning two mobjects). For convex hulls, call vanilla `manim.ConvexHull` -- Simplex no longer wraps it. |
| `GlyphMapTransform` | `engine.glyph_map` | `TransformByGlyphMap` -- explicit glyph-index morph |
| `TrackingHelpers` | `engine.dynamics` | `VT` (`~`/`@`), `DN`. Unit-vector math uses vanilla `manim.utils.space_ops.rotate_vector`. |
| `ShapeAndDebug` | `engine.geometry` + `engine.debug` + `engine.ghost_fade` | `SurroundingRectangleUnion`, `indexx_labels`, `bounding_box`, `GhostSlideFade` |
| `ScalingHelpers` | `engine.scaling` | `scale_to_fit(len_x, len_y, buff)`; demonstrates `Region.split` alongside |

## Notes

- For convex hulls, use Manim's built-in `ConvexHull` (QuickHull-based, no SciPy). Simplex no longer wraps it -- `from manim import ConvexHull`.
- `code_block` registers the Darcula Pygments style on first use; subsequent calls are a no-op.
- `code_with_math(src, ...)` replaces every `$...$` region in `src` with a `MathTex` glyph scaled to the surrounding code font (calibrated against a cached `Mq` reference, so `\infty` and `\bigcup_{i=1}^n` both land at the right size). Lines reflow so the rendered math width drives the layout, and the background is refit only when at least one substitution happens. Pass `bold_math=True` to wrap each match in `\boldsymbol{...}` and `math_color="..."` to recolour the math.
- `pseudocode_block(src, ...)` compiles a full `algorithm2e` algorithm (or wraps a body in `\begin{algorithm}[H]...\end{algorithm}`), then exposes the rendered numbered rows through `Code.code_lines`. That keeps `highlight_code_lines` and `code_explain` aligned with the visible algorithm line numbers. Pass `line_index="visible"` when caption/input/output rows should also be indexable.
- `TexPage` is the encapsulated prose helper (was `Definition`). Its default page width is the current full frame, with `LARGE_BUFF` removed from both sides before Simplex converts Manim units to LaTeX minipage centimeters. Pass `page_width=` as a number or `Region`, tune `buff=`, use `math_spacing=` for display-skip lengths, and call `equation(n)` to target a displayed `\[...\]` equation directly.
- Body-sized prose uses plain `manim.Tex`. The plugin's `apply_theme_defaults` sets the body `font_size` and `color` so `Tex(...)` already matches what the old `BodyText` produced.
- `region.place(mob, anchor, buff=...)` accepts a Manim direction vector (`UP`, `DR`, `ORIGIN`, ...) -- string anchors raise `ValueError`.
- `region.split_regions(axis, k)` returns `k` sub-regions strung along `axis` (e.g. `RIGHT` → left-to-right). Each piece keeps the perpendicular extent and gets `1/k` of the axis extent; their union is the original.
- Slide numbering and the wall clock live in the web player shell (toggle via `[web] show_slide_number` / `show_clock` in `deck.toml`). They are not drawn into each frame, so toggling them does not invalidate the Manim cache.
- The MF-Tools-derived helpers deliberately drop everything Manim 0.20.x already ships -- `ValueTracker` arithmetic operators, `index_labels`, `ConvexHull`, `Polygon.round_corners`, `Union`, `BraceLabel`/`BraceText`, `Mobject.always`, `manim.utils.space_ops.normalize` / `angle_of_vector` / `rotate_vector`, and `manim.constants.QUALITIES` all stay native. We only add what isn't already there.
- `TransformByGlyphMap` falls back to a `show_indices` mode if the leftover glyph counts don't line up -- pass an empty `glyph_map` (or `show_indices=True`) to see the index labels and write the right map.
- `VT` only adds `~vt`, `vt @ x`, `vt @= x`. The `+`, `-`, `*`, `/`, `**` operators are inherited from `ValueTracker` (added in Manim 0.19.1).
- `DN(callable_or_VT, ...)` attaches an `add_updater`, NOT `Mobject.always` -- the latter would snapshot the value once at attach time (a documented Manim gotcha).
- Prefer `self.slide(title="...")` and `self.fragment(title="...")`; Simplex derives stable cue ids from the main slide title and number. The older `next_slide()` helper is now only a thin Simplex cue alias.

## Callout references

> **Theorem.** \label{thm:simplex-callout}
> Theorem-style callouts are numbered automatically and can be referenced by label.

> **Definition.** \label{defn:simplex-region}
> A Simplex region is a rectangular anchor system that places Manim mobjects with consistent spacing.

Use `\ref{thm:simplex-callout}` for \ref{thm:simplex-callout}, and `\autoref{defn:simplex-region}` for \autoref{defn:simplex-region}. The notes PDF emits matching LaTeX theorem environments.

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
