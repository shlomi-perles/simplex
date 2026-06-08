# slides/

Slide classes + chrome factory built on `manim_slides`. Theme
defaults are applied by the `simplex.plugin:activate` entry-point, not
here.

## Public surface

- `Slide` -- `clear_scene(exclude=...)` and a hierarchy-aware `next_slide`:
  - `self.next_slide(name="Foo")` -> **main** slide named `"Foo"`.
  - `self.next_slide()` as the *first* call -> **main** auto-named
    after the scene class (silent; the name is the only thing that
    changes between auto-promotion and an explicit name).
  - `self.next_slide()` after a named main -> **sub-slide** of that main.
  - `loop=True` -> the `LOOP` variant; explicit `section_type=` always wins.
  - `wait_time_between_slides` defaults to `0.1`, applied before the native
    Manim section boundary and again at scene teardown, so every encoded
    segment keeps the final animation frame. Set `slide_boundary_wait_time = 0`
    on a subclass to disable the default.
- `OutlineScene` / `OutlinePart` -- reusable animated lecture outline
  scene. Progress dots are positioned through `Region.linspace(RIGHT, n)`
  defaults, not `arrange`, so edge margins and inter-dot gaps match the
  Simplex region contract.
- `self.setup_chrome(header=..., footer=..., theme=..., region=...)`
  -- convenience wrapper for the common setup path. If neither header nor
  footer is set, it returns without touching the scene; otherwise it calls
  `make_chrome`, registers the result in `add_to_canvas`, adds those
  mobjects to the scene so they render, registers them as fixed-frame
  mobjects when supported by a 3D scene, and updates `self.region`.
- `make_chrome(theme, region, *, header=..., footer=...)`
  -- *pure* factory returning a `Chrome(mobjects, body_region)`
  NamedTuple. `header` and `footer` can be strings or prebuilt Manim
  mobjects. Buff distances are read from `theme.spacing.header_buff` /
  `footer_buff`.
- `Chrome` -- the NamedTuple returned by `make_chrome`.
- `ThreeDSlide` -- the 3D equivalent of `Slide`, built on
  `manim_slides.ThreeDSlide`.
- `BaseSlide` -- compatibility alias for `Slide`; new decks should import
  `Slide`.

Slide numbering and a wall clock are presentation chrome, not rendered
chrome: they're driven by the RevealJS template / `[web]` deck overrides
(see `simplex.web`), so they survive without being re-rendered.

Reusable mobjects (`Node`, `Edge`, `Array`, ...) live in
`simplex.mobjects`, not here.

## Don't

- Don't put theme logic in subclasses. Read theme tokens via
  `get_active_theme()` inside `setup()`.
- Don't call `super().setup()` after touching `self.region` -- the
  base seeds it first.
- Don't subclass for chrome (header/footer); use `setup_chrome`.
- Don't mutate the `region` passed to `make_chrome` -- it is treated as
  immutable; the returned `body_region` is the shrunk copy.
