# Simplex showcase

This deck is the canonical reference for every helper Simplex adds on top of
vanilla Manim. Each scene targets one module; read alongside the matching
`README.md` in `src/simplex/`.

## What's exercised

| Scene | Module | Helpers |
|-------|--------|---------|
| `TextHelpers` | `engine.text` | `BodyText`, `Caption`, `Definition`, `color_tex` |
| `CodeHelpers` | `engine.code` | `code_block`, `highlight_code_lines`, `code_explain` |
| `GraphAndArray` | `slides.components` | `Node`, `Edge`, `ArrayMob`, `ArrayPointer` |
| `RegionAnchors` | `engine.region` | nine anchor names, `shrink`, `reset` |
| `ExitAnimations` | `engine.animations` | `set_exit_animation`, `clear_scene(exclude=...)` |
| `GeometryHelpers` | `engine.geometry` | `get_convex_hull_polygon`, `get_surrounding_rectangle` |

## Notes

- The convex-hull demo requires SciPy. Install it via `pip install simplex[geometry]`; without it, the scene shows a caption pointing readers to the extras.
- `code_block` registers the Darcula Pygments style on first use; subsequent calls are a no-op.
- `Definition` reads its TeX environment from `theme.latex.environments["definition"]`, which defaults to `{minipage}{8cm}` in `DASTIMATOR_DARK`. Override by constructing a fresh `Theme` rather than mutating tokens (they're frozen).

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
