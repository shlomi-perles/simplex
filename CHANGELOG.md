# Changelog

All notable changes to `manim-simplex` are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
