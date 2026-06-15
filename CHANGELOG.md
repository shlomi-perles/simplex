# Changelog

All notable changes to `manim-simplex` are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.15.0](https://github.com/shlomi-perles/simplex/compare/manim-simplex-v0.14.0...manim-simplex-v0.15.0) (2026-06-15)


### ⚠ BREAKING CHANGES

* PPTX export support and the exports.pptx manifest field were removed.

### Features

* **cli:** auto-select free serve port ([39eea98](https://github.com/shlomi-perles/simplex/commit/39eea983632135810d38a127099e0b6fc5a41713))
* make slide PDFs theme-aware ([0c58299](https://github.com/shlomi-perles/simplex/commit/0c582995ac724e3e7e0e13d5c7d70660dafb9c56))


### Bug Fixes

* **playback:** include leading scene frames in first cue ([dc9a152](https://github.com/shlomi-perles/simplex/commit/dc9a1524d326af39a7c65cf414336d3de24db7f8))
* **playback:** split legacy leading cue caches ([384e0b2](https://github.com/shlomi-perles/simplex/commit/384e0b285f34c2dddf8adb48d42135d1db5616b5))
* **player:** keep presentation cues authoritative ([4044c44](https://github.com/shlomi-perles/simplex/commit/4044c444bbeedcbdeb145826d992dd24a7aed054))
* **player:** require accurate cue seek landing ([ad50aa0](https://github.com/shlomi-perles/simplex/commit/ad50aa0451fb2009855272d5600fc23ec351ee82))
* **player:** stabilize presentation cue boundaries ([45235b3](https://github.com/shlomi-perles/simplex/commit/45235b3e7e2cd754e05091170834be98bd670170))
* **player:** start next main slide after subslide ([deadcdc](https://github.com/shlomi-perles/simplex/commit/deadcdc60f0c129f5f501eb5df54487a4cc97080))
* **render:** preserve Manim cache defaults ([18753b1](https://github.com/shlomi-perles/simplex/commit/18753b17bca655b2a19871fa4fa33d33be99724c))

## [0.14.0](https://github.com/shlomi-perles/simplex/compare/manim-simplex-v0.13.0...manim-simplex-v0.14.0) (2026-06-09)


### ⚠ BREAKING CHANGES

* **engine:** color_tex was renamed to color_substrings.
* **mobjects:** Edge now subclasses Manim Line directly; an optional weight label is the only child submobject.

### Features

* add algorithm pseudocode code blocks ([cebbed6](https://github.com/shlomi-perles/simplex/commit/cebbed612a0f5b0ce6e4e1e2538f97a485b0105c))
* **mobjects:** make edges line-native ([8980ec9](https://github.com/shlomi-perles/simplex/commit/8980ec9b8c6c7347addaa631578cafa0e6ddb8dc))
* **render:** package decks as timeline media ([18bc60e](https://github.com/shlomi-perles/simplex/commit/18bc60ef0b762e3d18174f252e1baaf67634e798))
* **slides:** add timeline cue authoring ([87dd528](https://github.com/shlomi-perles/simplex/commit/87dd5283c0eef32f325a2e2d59813d5124ce60ea))
* support global deck config and palette variants ([16eb9d7](https://github.com/shlomi-perles/simplex/commit/16eb9d77163e754a65951257329a94b14a53299c))
* **web:** replace reveal playback with timeline player ([be0b65c](https://github.com/shlomi-perles/simplex/commit/be0b65cd9e20487a6ab2f7bc127a0eb2ca8c8d9b))


### Bug Fixes

* **cli:** emit stable no-render manim flag error ([ec51efc](https://github.com/shlomi-perles/simplex/commit/ec51efcf54fcc503b1515e73c9403761b346d553))
* **manim:** stop forcing section output ([a9ee582](https://github.com/shlomi-perles/simplex/commit/a9ee582fd23ca1ecb99309835285d71e1fbc51e2))
* **mobjects:** preserve paper stack layout on pick ([5cf33f1](https://github.com/shlomi-perles/simplex/commit/5cf33f144bcf5adfd972869b8d2712b41a14ef83))
* **mobjects:** use opengl surface for sphere renders ([34b0537](https://github.com/shlomi-perles/simplex/commit/34b053748927ea5e73457cbd3e291b286170e9e5))
* **render:** avoid flaky manim-slides reverse videos ([2272fec](https://github.com/shlomi-perles/simplex/commit/2272fec57e6fd7ee811b13f9d9c193c874c4f864))
* **render:** pass manim flags through render and build ([164b18b](https://github.com/shlomi-perles/simplex/commit/164b18b5c2cef6ebd841f43dc0b8b6cfdbe5d500))
* scope algorithm2e template setup ([4c6d29e](https://github.com/shlomi-perles/simplex/commit/4c6d29e8a72b60462dd804839e82e534b54dbea5))
* **showcase:** preserve logo footer on clear ([1a56015](https://github.com/shlomi-perles/simplex/commit/1a56015e9c2a18bb13753601104c20269b6c87cb))
* **slides:** pad final slide segment at teardown ([a0890c5](https://github.com/shlomi-perles/simplex/commit/a0890c542bdb72c122b2b602aaa85ded3edce4f2))
* **theme:** centralize manim palette defaults ([486e394](https://github.com/shlomi-perles/simplex/commit/486e394a945fe8f4038bfb78d8bdff4530594605))
* **theme:** reserve edge styling for Edge ([0777ecb](https://github.com/shlomi-perles/simplex/commit/0777ecbbb82b0611143050cbfa41ed3c04f0a107))
* **theme:** restore latex preamble for simplex_light theme ([63d4f7d](https://github.com/shlomi-perles/simplex/commit/63d4f7d1995bc6b17ed2d2cbfc512df4c2c594e1))
* **types:** align manim typing contracts ([e16009e](https://github.com/shlomi-perles/simplex/commit/e16009e48cc40d41b6087f260acf4117a3715f1a))
* **types:** satisfy strict CI type checks ([b865213](https://github.com/shlomi-perles/simplex/commit/b8652131f60714fe6acf529f2f34e2d5a6480f36))
* **web:** match player load background to slide theme ([be3cd94](https://github.com/shlomi-perles/simplex/commit/be3cd940c4652a7e6a6e48d01ea08c6585f3485b))


### Documentation

* **examples:** update decks for timeline playback ([5fbe808](https://github.com/shlomi-perles/simplex/commit/5fbe8089d1220e07a1dc6d202367688a56608c55))


### Code Refactoring

* **engine:** tighten Manim helper typing ([ff9dd55](https://github.com/shlomi-perles/simplex/commit/ff9dd55daee76339fac2cb8f49a6d78e74747b1b))

## [0.13.0](https://github.com/shlomi-perles/simplex/compare/manim-simplex-v0.12.1...manim-simplex-v0.13.0) (2026-06-02)


### ⚠ BREAKING CHANGES

* **slides:** Region.always.place(...) has been removed. Use Region.always_place(...) to keep a mobject anchored to a Region.

### Features

* **engine:** improve TexPage and showcase layout helpers ([c7d9327](https://github.com/shlomi-perles/simplex/commit/c7d9327972f1b65c9a05acfd70cc53c7cb912570))
* **mobjects:** rewrite array mobject and animations ([79a1c09](https://github.com/shlomi-perles/simplex/commit/79a1c09255500e3333a2c9f293b87bc8e39376be))


### Bug Fixes

* **mobjects:** refine array mobject layout ([1f9cbf0](https://github.com/shlomi-perles/simplex/commit/1f9cbf0d550600e22ba7c322559b0ced2bf401d2))
* **opengl:** support showcase partial render smoke tests ([892f25f](https://github.com/shlomi-perles/simplex/commit/892f25f88cdf107805739d262dcc226d70333b73))
* **slides:** keep final frames inside slide sections ([50f68a4](https://github.com/shlomi-perles/simplex/commit/50f68a4cae42f3db713856e017b7315060870deb))
* **theme:** refine layout and theme defaults ([f7a6c72](https://github.com/shlomi-perles/simplex/commit/f7a6c72b3875b27d2402dc181160b39b3c199fda))


### Documentation

* **showcase:** refresh slide scenes ([368d930](https://github.com/shlomi-perles/simplex/commit/368d93021bd715e333862d03e2f874877c32448e))
* **showcase:** update showcase scenes ([ed36745](https://github.com/shlomi-perles/simplex/commit/ed367453f60ec427cdccc409dff6a378b05e313f))

## [0.12.1](https://github.com/shlomi-perles/simplex/compare/manim-simplex-v0.12.0...manim-simplex-v0.12.1) (2026-06-02)


### Bug Fixes

* use true start frames for deck previews ([3b7273f](https://github.com/shlomi-perles/simplex/commit/3b7273f958e82e648ace22c7041c3dae86a24f39))

## [0.12.0](https://github.com/shlomi-perles/simplex/compare/manim-simplex-v0.11.0...manim-simplex-v0.12.0) (2026-06-02)


### Features

* **web:** make deck assets theme-aware ([deeb954](https://github.com/shlomi-perles/simplex/commit/deeb9545ff96aa7aabb64094c76a8d37e3d34b7e))

## [0.11.0](https://github.com/shlomi-perles/simplex/compare/manim-simplex-v0.10.0...manim-simplex-v0.11.0) (2026-06-02)


### Features

* add palette-backed themes and theme studio ([b1dfbbc](https://github.com/shlomi-perles/simplex/commit/b1dfbbcbce585ee039147b33cd167e66c5d9d460))

## [0.10.0](https://github.com/shlomi-perles/simplex/compare/manim-simplex-v0.9.0...manim-simplex-v0.10.0) (2026-06-02)


### Features

* replace iframe deck player with direct media stage ([5e798a8](https://github.com/shlomi-perles/simplex/commit/5e798a81ecd956ac698e25449053ac0ff29c99c8))

## [0.9.0](https://github.com/shlomi-perles/simplex/compare/manim-simplex-v0.8.0...manim-simplex-v0.9.0) (2026-05-31)


### Features

* add true slide themes ([369b57f](https://github.com/shlomi-perles/simplex/commit/369b57f74e73f48f980ba3bfd1c6e1a8d31ff69b))

## [0.8.0](https://github.com/shlomi-perles/simplex/compare/manim-simplex-v0.7.0...manim-simplex-v0.8.0) (2026-05-31)


### Features

* add compact renderer entrypoint syntax ([4496222](https://github.com/shlomi-perles/simplex/commit/4496222fc047617992270673529a925d345656f1))

## [0.7.0](https://github.com/shlomi-perles/simplex/compare/manim-simplex-v0.6.0...manim-simplex-v0.7.0) (2026-05-31)


### Features

* add ManimCE OpenGL compatibility ([cbfcf2d](https://github.com/shlomi-perles/simplex/commit/cbfcf2dd36269d68e6f17e82297d37b8dc6a986d))
* add ScalarFieldSurface, ColorBar, and colorize_surface ([fb64295](https://github.com/shlomi-perles/simplex/commit/fb64295239772e969c3e2c282657bf19a77e03cc))
* enhance CI workflow with Manim health check and update scaling functions for stroke awareness ([256d81a](https://github.com/shlomi-perles/simplex/commit/256d81ad3629e7098cd5d988ff6ff52025b2c5cf))


### Bug Fixes

* add type annotations to surface.py to resolve basedpyright errors ([09439f8](https://github.com/shlomi-perles/simplex/commit/09439f8f58ead9be3a4ece366847aa8576e2a1f1))
* **ci:** pipe 'n' to manim checkhealth to avoid interactive prompt ([3ec06e0](https://github.com/shlomi-perles/simplex/commit/3ec06e08b2ffd033dd872c5254cae3778a376176))
* interpolate vertex colors smoothly during animations ([0f8befe](https://github.com/shlomi-perles/simplex/commit/0f8befeff0a55c7da0bc61308be8b3398c60e195))
* satisfy OpenGL compatibility type checks ([521a50d](https://github.com/shlomi-perles/simplex/commit/521a50dd8d2099bdbfda2800b8401ee9af403e3f))
* skip OpenGL smoke renders in headless CI ([f5aa90e](https://github.com/shlomi-perles/simplex/commit/f5aa90ef611e8f2adaf97bce15047ee2e6aecad8))

## [0.6.0](https://github.com/shlomi-perles/simplex/compare/manim-simplex-v0.5.0...manim-simplex-v0.6.0) (2026-05-26)


### ⚠ BREAKING CHANGES

* drop Manim 0.20.x reimplementations

### Features

* **dynamics:** enhance keep_orientation function for improved stability and clarity ([a68e982](https://github.com/shlomi-perles/simplex/commit/a68e9823ba95f80e0ca9828bae8b5ce3e8f9cd18))
* **dynamics:** improve keep_orientation function to maintain object position during rotation ([fb8ed73](https://github.com/shlomi-perles/simplex/commit/fb8ed73c018a69d0cd0b5b2430774de8a33a1394))
* **styles:** update color codes for SimplexPycharm and add bold style for Token in SimplexSolarizedLight ([22a0e0f](https://github.com/shlomi-perles/simplex/commit/22a0e0f85c847560ee9e953dca04ff36856c950e))
* **styles:** update Name color in SimplexPycharm style for improved visibility ([db68ce9](https://github.com/shlomi-perles/simplex/commit/db68ce9cfef6311c8d8ebff521a797da10296bad))
* **styles:** update Token style to use double quotes for consistency ([11d6eab](https://github.com/shlomi-perles/simplex/commit/11d6eabe90508be42e36fe8ef5675182b5e6905d))


### Bug Fixes

* **docs:** correct header formatting in README.md for decks section ([0d6d7cd](https://github.com/shlomi-perles/simplex/commit/0d6d7cde3327a40b9a04e357518fc3f968be195f))
* **dynamics:** update _upright function to use original mobject for boundary points ([bd0fd44](https://github.com/shlomi-perles/simplex/commit/bd0fd44f6172422fda1fb9e1e9f6c3c468907d50))


### Documentation

* update README.md for improved clarity and structure ([5594a4a](https://github.com/shlomi-perles/simplex/commit/5594a4adf8f37c54dfccc1e13365b380476658de))


### Code Refactoring

* drop Manim 0.20.x reimplementations ([f28b0ff](https://github.com/shlomi-perles/simplex/commit/f28b0ff3ffb66f05c7ea79e68e391c108ae54fa4))

## [0.5.0](https://github.com/shlomi-perles/simplex/compare/manim-simplex-v0.4.1...manim-simplex-v0.5.0) (2026-05-26)


### ⚠ BREAKING CHANGES

* Region is no longer a Pydantic model; the read-only `center`/`width`/`height` properties are gone -- use the inherited Rectangle methods (`get_center()`, `width`, `height` still work via the Mobject API). Region.split is renamed Region.split_regions to free `split` for future Manim parity. make_chrome's header/footer parameters widened from `str | None` to `str | Mobject | None`.

### Features

* chrome ergonomics, Region as Rectangle, paper polish, showcase rewrite ([346ef5b](https://github.com/shlomi-perles/simplex/commit/346ef5b02de4118e72efbf24f2bd92e8ea178f0b))
* **mobjects:** add blurred paper shadows ([37df25f](https://github.com/shlomi-perles/simplex/commit/37df25f589d6a9eb0300affbf346479f7dda88b3))

## [0.4.1](https://github.com/shlomi-perles/simplex/compare/manim-simplex-v0.4.0...manim-simplex-v0.4.1) (2026-05-25)

### Added

- Stopwatch player chrome with settings controls for show/hide, start/stop,
  and reset. The stopwatch renders next to the clock when visible and in the
  same corner when the clock is hidden.
- Deck-level `[web] notes_code_style` override for markdown notes code blocks.

### Changed

- Space now toggles playback, while Ctrl+Right and Ctrl+Left jump between main
  slides with sub-slide reset behavior on Ctrl+Left.
- Mobile slide taps now use seamless transparent tap zones backed by pointer
  events for both embedded and fullscreen playback.
- Player settings are ordered as Enumeration, Clock, Stopwatch, and Theme.
- Markdown notes code blocks default to `SimplexSolarizedLight`, independent
  of the slide theme.
- Notes PDF export now loads `hyperref` with bookmark/link options and the
  Simplex color definitions, including green citation links.

### Fixed

- Bibliography HTML no longer uses an ordered list, so references display as
  `[KB15]` markers without numeric enumeration.

## [0.3.1](https://github.com/shlomi-perles/simplex/compare/manim-simplex-v0.3.0...manim-simplex-v0.3.1) (2026-05-25)


### Bug Fixes

* **ci:** keep release lockfile in sync ([#28](https://github.com/shlomi-perles/simplex/issues/28)) ([55bbc9f](https://github.com/shlomi-perles/simplex/commit/55bbc9fe1ef64e8d431b72b9f8e2f7743c65eaaa))

## [0.3.0](https://github.com/shlomi-perles/simplex/compare/manim-simplex-v0.2.3...manim-simplex-v0.3.0) (2026-05-25)


### Features

* consolidate Simplex package ([7e1aedb](https://github.com/shlomi-perles/simplex/commit/7e1aedbf646e9d90ffb2fc22a852e5a5d3042e75))
* enhance media handling and presentation features ([9dff7cc](https://github.com/shlomi-perles/simplex/commit/9dff7ccfc4bfbe79f5bffd1c01d0bac090207399))


### Bug Fixes

* handle string duration in _row_duration and update tests for consistency ([612fd3c](https://github.com/shlomi-perles/simplex/commit/612fd3c24e1c9c3ee7dbbe1a42080211ba6c927d))

## [Unreleased]

### Added

- `simplex` CLI, deck discovery/scaffolding, render orchestration, static web
  portal builder, notes/citation rendering, and bundled deck template now ship
  inside `manim-simplex`.
- Release Please configuration and release workflow for uv builds, PyPI
  Trusted Publishing, and template update dispatch.
- Renovate configuration for dependency and lockfile maintenance.

### Changed

- **BREAKING:** `manim-simplex` is now the only PyPI distribution that owns the
  `simplex` package namespace. The former `simplex-web` package is folded into
  this distribution.
- CI now checks the CLI/web stack, vendors web assets before wheel builds, and
  smoke-renders the bundled showcase deck.

## [0.2.3] - 2026-05-25

### Added

- Top-level authoring imports such as `from simplex import BaseSlide, Caption`.

### Changed

- Rename the default theme from `dastimator_dark` / `DASTIMATOR_DARK` to
  `simplex_dark` / `SIMPLEX_DARK`.

## [0.2.1] - 2026-05-24

### Changed

- Highlight Pygments word operators in the Darcula code style.

## [0.2.0] - 2026-05-24

### Added

- `TexPage` mobject — fixed-width minipage helper. Width is configurable
  via the ``width_cm`` kwarg (default 20.0) or by overriding the class
  attribute on a subclass. Replaces the old ``Definition`` mobject; the
  hardcoded minipage literal no longer appears in presets or
  tests.
- `Region.split(axis, k)` — divide a region into ``k`` sub-regions
  along a cardinal direction. Each piece keeps the perpendicular extent
  and gets ``1/k`` of the axis extent; pieces are returned in the
  direction of ``axis``. Their union equals the original region.
- `Spacing.header_buff` / `Spacing.footer_buff` — chrome gap distances
  exposed on the theme so they can be tuned deck-wide without editing
  ``make_chrome``.
- `simplex.manifest` module — Pydantic models (`DeckManifest`, `MainSlide`,
  `Subsection`) that define the cross-package contract between the plugin
  and the `simplex` web builder. The web builder now imports the schema
  from the plugin rather than redefining it locally.
- `simplex.section` module — `SimplexSectionType` enum promoted to the
  package root (previously `simplex.engine.section_types`). Manim-free so
  the web builder and CLI can use it without paying for a Manim import.
- `simplex.mobjects` subpackage — `Node`, `Edge`, `ArrayMob`, `ArrayEntry`,
  `ArrayPointer` promoted from `simplex.slides.components` to a top-level
  mobjects package, matching Manim's own `manim.mobject.*` convention.
- `simplex.slides.Chrome` NamedTuple — pure factory return type combining
  the canvas mobjects dict and the body region.
- `simplex.engine.HighlightResult` dataclass — typed return for
  `highlight_code_lines`, iterable so the existing `self.play(*result)`
  pattern still works.
- `py.typed` marker — downstream `pyright`/`mypy` users now get type
  information for the `simplex` namespace.
- `examples/` directory — runnable demo scenes (`hello_slide.py`,
  `theme_demo.py`, `glyph_map_demo.py`) used as documentation and CI
  fixtures.
- `.pre-commit-config.yaml` — ruff, ruff-format, codespell, and standard
  whitespace/yaml/toml hygiene hooks.
- CHANGELOG.md.
- CI: `manim plugins -l` discovery smoke test alongside the existing
  import smoke.

### Changed

- **BREAKING:** ``Region.place`` now takes a Manim **direction vector**
  (``UP``, ``DR``, ``ORIGIN``, …) instead of a string anchor name. The
  same applies to the ``_anchor_point`` helper. Migrate
  ``region.place(mob, "top", buff=…)`` → ``region.place(mob, UP, buff=…)``.
- **BREAKING:** ``make_chrome`` no longer accepts a ``page=`` parameter.
  Slide numbering is presentation chrome and is now driven by the
  RevealJS template (toggle via ``[web]`` overrides in ``deck.toml``)
  so it survives without being baked into each frame.
- **BREAKING:** ``BodyText`` is removed. Plain ``manim.Tex`` carries the
  theme's body font size through ``apply_theme_defaults`` — call sites
  rewrite ``BodyText(...)`` to ``Tex(...)``.
- **BREAKING:** ``Definition`` is renamed to ``TexPage`` (and no longer
  reads ``theme.latex.environments["definition"]``).
- ``BaseSlide`` auto-promotion now pretty-prints the class name into a
  space-separated label (``DFSLecture`` → ``"DFS Lecture"``,
  ``ImplementBFSSlide`` → ``"Implement BFS Slide"``). The class name
  itself is unchanged.
- **BREAKING:** Python floor raised to **3.13** (was a transitional 3.14
  in the Phase 3 split commit). 3.13 is a long-term-supportable floor
  with much wider availability for lecture authors.
- **BREAKING:** `simplex.engine.section_types` → `simplex.section`.
- **BREAKING:** `simplex.slides.components.{graph, array}` →
  `simplex.mobjects.{graph, array}`.
- **BREAKING:** `simplex.engine.transforms` is split into
  `simplex.engine.glyph_map` (`TransformByGlyphMap`) and
  `simplex.engine.ghost_fade` (`GhostSlideFade`). The combined module is
  removed.
- `BaseSlide.next_slide()` still auto-promotes the first bare call to
  a main slide (named after the scene class), but no longer emits a
  `UserWarning`. Passing `name=` on the first call still works and only
  changes the slide's name; the section type is `MAIN` either way.
- **BREAKING:** `make_chrome` no longer mutates its `Region` argument.
  It returns a `Chrome(mobjects, body_region)` NamedTuple. Callers do
  `chrome = make_chrome(...); self.add_to_canvas(**chrome.mobjects);
  self.region = chrome.body_region` (or destructure).
- **BREAKING:** `highlight_code_lines` returns `HighlightResult` (a
  frozen dataclass with `.fade` and `.indicate`) instead of the prior
  tuple-or-AnimationGroup union. `*result` unpacks back into the
  previous tuple form for callers that prefer it.
- Exit animation overrides are now stored in a `WeakKeyDictionary`
  registry rather than monkey-patched onto the `Mobject` as a
  `_simplex_exit` attribute. The public API (`set_exit_animation`,
  `exit_for`, `Remove`) is unchanged.
- The exit-defaults registry is now wrapped in a singleton with
  threading.Lock-guarded lazy init, removing the module-level mutable
  global.

### Removed

- ``BodyText`` mobject. Use ``manim.Tex`` (body size + color come from
  ``apply_theme_defaults``) or ``Caption`` for smaller annotations.
- ``Definition`` mobject. Replaced by ``TexPage`` (see Added/Changed).
- ``make_chrome(..., page=…)`` parameter and the corresponding ``page``
  entry in ``Chrome.mobjects``. Slide numbering moves to the web layer.
- ``LatexProfile.environments["definition"]`` entries from
  ``SIMPLEX_DARK`` and ``ACADEMIC_LIGHT``: ``TexPage`` is now the
  single owner of the ``{minipage}{<width>cm}`` literal.
- `simplex.engine.section_types` module (replaced by `simplex.section`).
- `simplex.slides.components` subpackage (replaced by `simplex.mobjects`).
- `simplex.engine.transforms` module (split — see Changed).
- `UserWarning` on the first bare `BaseSlide.next_slide()` call. Auto-
  promotion stays (named after the class), just silently.
