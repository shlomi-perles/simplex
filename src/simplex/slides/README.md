# slides/

Slide base classes built on `manim_slides.Slide`. Each base wires the active theme, applies defaults, and seeds `self.region = Region.full_frame()` in `setup()`.

## Public surface

- `BaseSlide` -- theme push + `clear_scene(exclude=...)`
- `ContentSlide` -- header / footer / page number; shrinks `self.region` accordingly
- `slides.components` -- `Node`, `Edge`, `ArrayMob`

## Don't

- Don't put theme logic in subclasses. Read theme tokens via `get_active_theme()`.
- Don't call `super().setup()` after touching `self.region` -- the base seeds it first.
