# slides/components/

Higher-level domain mobjects (graphs, arrays). All subclass `VMobject` directly -- no Manim wrapping.

## Public surface

- `Node(label)` -- circle + centered label, reads colors from the active theme
- `Edge(start, end, weight=None)` -- line + optional weight label
- `ArrayMob(values)` -- a row of cells with centered content

## Don't

- Don't read from `config.frame_width` for sizing. Use theme tokens or absolute units.
- Don't add a constructor parameter for color overrides; tune the active theme instead.
