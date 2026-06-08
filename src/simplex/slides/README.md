# slides/

Simplex-owned Manim scene bases and chrome helpers.

## Public Surface

- `SimplexScene` / `SimplexThreeDScene` inherit directly from Manim Community
  `Scene` / `ThreeDScene`.
- `self.slide(id, title=..., notes=...)` records a primary cue.
- `self.fragment(id, title=..., notes=...)` records a sub-stop within the
  current slide.
- `self.loop(id, title=..., notes=...)` records a cue that loops in
  presentation mode.
- `self.skip(id, title=..., notes=...)` records a cue that exports may skip.
- `self.setup_chrome(...)`, `Chrome`, and `make_chrome(...)` provide the
  header/footer and region helpers.
- `Slide`, `ThreeDSlide`, and `BaseSlide` are aliases for the new Simplex
  scene bases.

Cue metadata is written beside rendered scene units by `SimplexScene`; it is
not sourced from Manim section JSON and does not call manim-slides.

## Don't

- Don't call Manim `next_section()` for playback metadata.
- Don't subclass for chrome; use `setup_chrome`.
- Don't put theme logic in subclasses. Read theme tokens via
  `get_active_theme()` inside `construct()` or `setup()`.
