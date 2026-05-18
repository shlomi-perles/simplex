# slides/

Slide base classes built on `manim_slides.Slide`. Theme defaults are applied by
the `simplex.plugin:activate` entry-point, not here.

## Public surface

- `BaseSlide` -- `clear_scene(exclude=...)` and a hierarchy-aware `next_slide`:
  - `self.next_slide(name="Foo")` -> **main** slide named "Foo"
  - `self.next_slide()` -> **sub-slide** of the previous main (first bare call auto-promotes to a main + warns)
  - `loop=True` flips the LOOP variant; explicit `section_type=` always wins
- `make_chrome(theme, region, *, header=..., footer=..., page=...)` -- factory that returns a `dict[str, Mobject]` for `add_to_canvas` and shrinks `region` to the body band
- `slides.components` -- `Node`, `Edge`, `ArrayMob`, `ArrayPointer`

## Don't

- Don't put theme logic in subclasses. Read theme tokens via `get_active_theme()` inside `setup()`.
- Don't call `super().setup()` after touching `self.region` -- the base seeds it first.
- Don't subclass for chrome (header/footer/page); use `make_chrome` and `add_to_canvas(**...)`.
