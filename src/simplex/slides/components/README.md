# slides/components/

Higher-level domain mobjects. All subclass `VMobject` / `VGroup` directly -- no Manim wrapping.

## Public surface

- `Node(label, radius=0.35)` -- circle + centered label, reads colors from the active theme. Default exit: `ShrinkToCenter`.
- `Edge(start, end, weight=None)` -- line + optional weight label
- `ArrayMob(name, *values, show_indices=False, starting_index=0, ...)` -- a named row of cells
  - `.at(index, value)` -- synchronous value update (returns the ArrayEntry)
  - `.indicate_at(index, color=None)` -- AnimationGroup with `Indicate`
  - `.push(value, side=RIGHT)`, `.pop(index=None, shift=DOWN)`, `.swap(i, j)` -- animations
- `ArrayEntry(value, index)` -- one cell (frame + value + index)
- `ArrayPointer(array, index, text=None, direction=DOWN)` -- arrow tied to an entry; `.to_entry(new_index)` animates the move

## Don't

- Don't read from `config.frame_width` for sizing. Use theme tokens or absolute units.
- Don't add a constructor parameter for color overrides; tune the active theme instead.
- Don't subclass `Mobject` directly -- inherit from `VMobject` / `VGroup` so Manim's animation machinery works.
