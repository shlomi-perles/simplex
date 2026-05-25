# slides/

Slide base class + chrome factory built on `manim_slides.Slide`. Theme
defaults are applied by the `simplex.plugin:activate` entry-point, not
here.

## Public surface

- `BaseSlide` -- `clear_scene(exclude=...)` and a hierarchy-aware `next_slide`:
  - `self.next_slide(name="Foo")` -> **main** slide named `"Foo"`.
  - `self.next_slide()` as the *first* call -> **main** auto-named
    after the scene class (silent; the name is the only thing that
    changes between auto-promotion and an explicit name).
  - `self.next_slide()` after a named main -> **sub-slide** of that main.
  - `loop=True` -> the `LOOP` variant; explicit `section_type=` always wins.
- `OutlineScene` / `OutlinePart` -- reusable animated lecture outline
  scene. Progress dots are positioned through `Region.linspace(RIGHT, n)`
  defaults, not `arrange`, so edge margins and inter-dot gaps match the
  Simplex region contract.
- `make_chrome(theme, region, *, header=..., footer=...)`
  -- *pure* factory returning a `Chrome(mobjects, body_region)`
  NamedTuple. Splat `chrome.mobjects` into `add_to_canvas` and assign
  `chrome.body_region` to `self.region`. Buff distances are read from
  `theme.spacing.header_buff` / `footer_buff`.
- `Chrome` -- the NamedTuple returned by `make_chrome`.

Slide numbering and a wall clock are presentation chrome, not rendered
chrome: they're driven by the RevealJS template / `[web]` deck overrides
(see `simplex.web`), so they survive without being re-rendered.

Re-usable mobjects (`Node`, `Edge`, `ArrayMob`, ...) live in
`simplex.mobjects`, not here.

## Don't

- Don't put theme logic in subclasses. Read theme tokens via
  `get_active_theme()` inside `setup()`.
- Don't call `super().setup()` after touching `self.region` -- the
  base seeds it first.
- Don't subclass for chrome (header/footer); use `make_chrome`
  and `add_to_canvas(**chrome.mobjects)`.
- Don't mutate the `region` passed to `make_chrome` -- it is treated as
  immutable; the returned `body_region` is the shrunk copy.
