# Simplex v0.2.0 Re-architecture Plan

This document captures the v0.2.0 rewrite agreed with the maintainer in
May 2026. It supersedes `PLAN.md` (kept as-is for historical context).

The four locked-in decisions that frame everything:

1. **Three repos**: `simplex-core` (PyPI `manim-simplex`), `simplex` (PyPI
   `simplex`, this repo), `simplex-lectures-template` (GitHub Template).
2. **Aggressive plugin**: `simplex.plugin:activate` sets `tex_template`,
   `background_color`, `save_sections=True`, registers Pygments style.
3. **`next_slide(name=...)` triggers MAIN; bare `next_slide()` is SUB**.
   First bare call auto-promotes to a MAIN with the class name + warning.
4. **Full rewrite, no backwards-compat shims**. v0.2.0 is a clean break.

---

## 1. Why we are doing this

The current architecture (PLAN.md) made these mistakes:

- **`slides/base.py:35-43` env-var pre-init** runs `configure_manim` per
  scene *before* `super().__init__()` to dodge a Manim timing bug. Every
  deck must be invoked through `simplex render` (which sets the env vars)
  or the theme silently vanishes.
- **`render/cache.py` reimplements caching** that manim already does at
  the per-animation level. Worse, it's coarser: a single source edit
  invalidates the whole deck.
- **`render/manifest.py` parses manim-slides JSON only**, missing manim's
  native sections metadata that already carries `name` and `section_type`.
- **`render/html.py` shell-copies video segments** and bypasses
  `manim_slides.convert.RevealJS` — a class we already depend on.
- **`slides/content.py::ContentSlide` chrome via subclassing** is not
  composable; you can't have header+region overrides without inheritance.
- The whole package is one wheel, even though the **manim plugin**
  surface (mobjects + theme + plugin entry) is reusable independently of
  the **lecture-portal CLI** (build, deploy, watch).

v0.2.0 fixes all six.

---

## 2. Three-repo split

### Repo A — `simplex-core` (PyPI: `manim-simplex`)

Pure manim plugin. Custom mobjects, theme tokens, `BaseSlide`,
`make_chrome`, the `DEFAULT_EXITS` registry, the `simplex.plugin:activate`
entry-point. No CLI, no web builder, no deck config.

Module surface under PEP 420 namespace `simplex/`:
- `simplex.plugin`         — `activate()` entry-point
- `simplex.section_types`  — `SimplexSectionType` enum
- `simplex.engine.*`       — animations (with `DEFAULT_EXITS`), transforms,
  dynamics, region, code, text, geometry, debug, scaling
- `simplex.theme.*`        — tokens (incl. `WebPalette`), presets,
  context, `web_css`, `pygments_style`
- `simplex.slides.*`       — `BaseSlide`, `chrome.make_chrome`,
  `components.{graph,array}`

### Repo B — `simplex` (PyPI: `simplex`, this repo after rewrite)

The lecture-portal platform. Depends on `manim-simplex`. Owns CLI, deck
discovery + scaffold, render orchestration, reconcile, web builder.

Module surface under same PEP 420 namespace `simplex/`:
- `simplex.cli.*`     — typer commands: `new | init | render | build |
  serve | test | clean | doctor`
- `simplex.deck.*`    — `DeckConfig` (with `SlideOverride`, `WebOverride`),
  `registry`, `section`, `scaffold`
- `simplex.render.*`  — `runner` (subprocess), `reconcile` (native section
  JSON), `html`/`pdf`/`pptx` (in-process via `manim_slides.convert`),
  `thumbnail`
- `simplex.web.*`     — `builder`, `notes`, bibliography stack, templates,
  static, SSE reload endpoint

### Repo C — `simplex-lectures-template` (GitHub Template)

Pre-wired user lectures repo. `pyproject.toml` pins `simplex>=0.2`,
`.github/workflows/deploy.yml` uses `actions/deploy-pages@v4`, one
minimal example deck. Users `gh repo create my-lectures
--template shlomi-perles/simplex-lectures-template`.

### PEP 420 namespace mechanics

Neither A nor B ships `src/simplex/__init__.py`. Python merges the
two distributions at import time. `from simplex.engine import Remove`
works regardless of which wheel ships it.

---

## 3. The plugin (Repo A)

`src/simplex/plugin.py::activate()` runs once per `import manim`:

```python
def activate() -> None:
    import manim
    from simplex.theme.context import get_active_theme
    from simplex.engine.defaults import apply_theme_defaults
    from simplex.theme.pygments_style import register_darcula
    theme = get_active_theme()
    apply_theme_defaults(theme)
    manim.config.tex_template = theme.latex.as_tex_template()
    manim.config.background_color = theme.palette.background
    manim.config.save_sections = True
    register_darcula()
```

Each deck's `manim.cfg`:

```ini
[CLI]
plugins = simplex
save_sections = True
```

Per-deck theme selection happens before manim is imported: the CLI
runner sets `theme/context::active_theme(...)` based on `deck.toml`'s
`theme` field, then spawns the subprocess.

---

## 4. Slide hierarchy

`SimplexSectionType(str, Enum)`:

| Value             | Meaning                          |
|-------------------|----------------------------------|
| `simplex.main`    | A main slide                     |
| `simplex.sub`     | A sub-slide of the previous main |
| `simplex.main.loop` | main + manim-slides loop       |
| `simplex.sub.loop`  | sub  + manim-slides loop       |
| `simplex.main.skip` | main, skip in playback         |
| `simplex.sub.skip`  | sub, skip in playback          |

`BaseSlide.next_slide(name=None, *, section_type=None, loop=False, **kw)`:

- `name=` set, no `section_type=` → MAIN (or MAIN_LOOP if `loop=True`)
- `name=` unset, no `section_type=`, first call → auto-promote to MAIN
  with class name + `warnings.warn`
- `name=` unset, no `section_type=`, subsequent → SUB (or SUB_LOOP)
- explicit `section_type=` always wins

The string value of `section_type` round-trips through
`Slide.next_slide → Scene.next_section → Section(type_=) → JSON "type"`.

`direction="vertical"` is set automatically on SUB rows so RevealJS
treats them as a vertical stack (up/down arrows).

---

## 5. Smart compilation

`config.save_sections = True` makes manim write
`<media>/videos/<src>/<q>/sections/<Scene>.json` plus one MP4 per
section. Combined with manim's existing per-animation hash cache
(`SceneFileWriter.is_already_cached`), this gives slide-level
incremental rendering for free.

Concrete consequence: re-editing one animation in a scene re-encodes
only that animation; sections containing only cached animations are
stitched from the cache. Wall-clock re-renders drop from O(scene) to
O(touched animation).

`render/cache.py` (sha256-stamp-the-whole-deck) is deleted. The
`--force` flag is removed.

---

## 6. Reconciliation

`render/reconcile.py` reads two JSON sources written by manim and
manim-slides:

| File                                          | Written by  | Carries                                              |
|-----------------------------------------------|-------------|------------------------------------------------------|
| `media/videos/<src>/<q>/sections/<Scene>.json`| manim       | `name`, `type` (our SimplexSectionType), duration    |
| `slides/<Scene>.json`                          | manim-slides| media paths, presentation config                     |

Reconciliation groups consecutive section entries by `type.startswith(
"simplex.main")` → MainSlide rows; everything else attaches as
sub-sections. Duration = sum of sub-section durations. Thumbnail =
last frame of `sub_sections[deck.slides[name].thumbnail_section_index]`,
default `-2`.

---

## 7. Default exit registry

`engine/animations.py` exposes:

```python
DEFAULT_EXITS: dict[type, Callable[[Mobject], Animation]] = {
    Tex: Unwrite, MathTex: Unwrite, Text: Unwrite, Code: Unwrite,
    Circle: ShrinkToCenter, Dot: ShrinkToCenter,
    Line: Uncreate, Arrow: Uncreate, DashedLine: Uncreate,
    VMobject: lambda m: FadeOut(m, shift=0.1 * DOWN),
}
def register_exit(t: type, factory: Callable) -> None: ...
def exit_for(m: Mobject) -> Animation: ...   # _simplex_exit > MRO > FadeOut
def Remove(m, **kw) -> Animation: return exit_for(m)
def clear_scene(scene, *, exclude=()) -> None: ...
```

`set_exit_animation(m, anim_cls_or_factory)` survives and stashes onto
`_simplex_exit`. `Remove(m)` dispatches via `exit_for(m)`. The
free-function `clear_scene(scene, *, exclude)` lives on the engine
namespace; `BaseSlide.clear_scene` is a thin delegate.

---

## 8. In-process conversion

`manim_slides.convert.{RevealJS, PDF, PowerPoint}` are plain classes
that take `presentation_configs: list[PresentationConfig]` and a
`convert_to(dest_path)` method. Subprocess invocation is wasteful.

`render/html.py` becomes:

```python
from manim_slides.convert import RevealJS
RevealJS(presentation_configs=cfgs, template=tpl).convert_to(dest_html)
```

`render/pdf.py` becomes:

```python
from manim_slides.convert import PDF
PDF(presentation_configs=cfgs).convert_to(dest_pdf)
```

New `render/pptx.py` does `PowerPoint(...).convert_to(...)`.

The custom `_copy_segments` flow in current `render/html.py` is
deleted; RevealJS handles segment URLs relatively already.

---

## 9. Web palette

`theme/tokens.py` adds:

```python
class WebPalette(BaseModel):
    accent: str; background: str; surface: str
    text_primary: str; text_muted: str; link: str
    code_background: str
    font_family_sans: str; font_family_mono: str
    font_size_base: str
```

`Theme.web_palette: WebPalette` field. `presets.py` fills defaults for
DASTIMATOR_DARK + ACADEMIC_LIGHT.

`theme/web_css.py::render_web_css(palette) -> str` emits a `:root {
--simplex-… }` block consumed by:
1. Portal `index.html` `<head>` (homepage cards, section pages)
2. Per-deck RevealJS HTML `<head>` (slide chrome, captions)

Per-deck override `[web]` in `deck.toml` (field-by-field; non-`None`
wins over theme defaults). `[web] custom_css_path` appended verbatim.
`[web] template` is a full RevealJS template escape hatch.

---

## 10. `deck.toml` schema

```toml
slug = "showcase"
title = "Simplex showcase"
summary = "Demonstrates every helper."
tags = ["reference"]
category = "Reference"
order = 0
theme = "dastimator_dark"

# Render controls
quality = "medium_quality"
render_quality_dev = "low_quality"
render_quality_release = "high_quality"
caching = true
self_test = false
voiceover = false

entrypoints = ["slides.scenes:TextHelpers", ...]

# Optional: override source order
slide_order = ["Main: Intro", "Main: Setup", "Main: Conclusion"]

# Per-main-slide tweaks (keyed by name= passed to next_slide)
[slides."Main: Intro"]
thumbnail_section_index = -1
notes_anchor = "intro"

[slides."Main: Architecture"]
thumbnail = "assets/hero.png"

# Per-deck portal + RevealJS overrides — all optional
[web]
accent = "#FF6B6B"
transition = "fade"
custom_css_path = "extra.css"
```

---

## 11. CLI surface

| Command                                  | Status   | Behaviour                                                                |
|------------------------------------------|----------|--------------------------------------------------------------------------|
| `simplex doctor`                         | keep     | latex / ffmpeg / manim / manim-slides on PATH                            |
| `simplex new [category/]slug`            | keep     | scaffold deck; rich.prompt for interactive flow                          |
| `simplex render slug[::Scene[::Main]]`   | refactor | manim cache does the work; `--force` gone                                |
| `simplex build [--only slug ...]`        | refactor | full pipeline; `--force` gone                                            |
| `simplex serve [--port N] [--watch]`     | extend   | `--watch` adds watchfiles + SSE reload                                   |
| `simplex test`                           | NEW      | `manim --write_last_frame --quality l` smoke for every deck              |
| `simplex clean [slug]`                   | keep     | wipe `media/`, `site/` (and `.simplex_cache/` while it still exists)     |
| `simplex init [target_dir]`              | NEW      | `gh repo create --template shlomi-perles/simplex-lectures-template`      |
| ~~`simplex deploy`~~                     | DROPPED  | replaced by `actions/deploy-pages@v4` in the template repo               |
| ~~`simplex thumbs`~~                     | DROPPED  | thumbnails come from sections JSON                                       |
| ~~`simplex render --force`~~             | DROPPED  | manim's per-animation cache is enough                                    |

---

## 12. CI / deploy

### `simplex/.github/workflows/ci.yml`

Lint, type-check, test, plus a render-smoke step that runs
`simplex test` over `decks/showcase/` to catch regressions.

### `simplex-lectures-template/.github/workflows/deploy.yml`

Uses `actions/upload-pages-artifact@v3` + `actions/deploy-pages@v4`. No
`gh-pages` branch, no `ghp-import`, no `peaceiris/actions-gh-pages`.

```yaml
on: { push: { branches: [main] }, workflow_dispatch: }
permissions: { contents: read, pages: write, id-token: write }
concurrency: { group: pages, cancel-in-progress: true }
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
      - run: sudo apt-get install -y texlive-latex-extra texlive-fonts-extra ffmpeg
      - run: uv sync
      - uses: actions/cache@v4
        with:
          path: [ "media/", "~/.cache/uv" ]
          key: simplex-${{ hashFiles('uv.lock','decks/**/deck.toml','decks/**/slides/**/*.py','decks/**/manim.cfg') }}
      - run: uv run simplex build
      - uses: actions/upload-pages-artifact@v3
        with: { path: site }
  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment: { name: github-pages, url: ${{ steps.deployment.outputs.page_url }} }
    steps: [ { uses: actions/deploy-pages@v4, id: deployment } ]
```

---

## 13. Tech stack

| Concern                  | Library                             | Status   |
|--------------------------|-------------------------------------|----------|
| Env + lockfile + Python  | uv                                  | kept     |
| Validation               | pydantic v2                         | kept     |
| Settings                 | pydantic-settings                   | kept     |
| CLI                      | typer + rich.prompt                 | kept     |
| File watcher             | watchfiles                          | NEW      |
| Logging                  | structlog                           | kept     |
| Lint                     | ruff (+ decks carve-out)            | kept     |
| Types                    | basedpyright --strict               | kept     |
| Tests                    | pytest + pytest-xdist + syrupy      | kept     |
| Markdown → HTML          | markdown-it-py + mdit-py-plugins    | kept     |
| Math (client)            | KaTeX (vendored)                    | kept     |
| Templating               | jinja2                              | kept     |
| Syntax highlight         | pygments                            | kept     |
| Render engine            | manim ≥ 0.20.1, manim-slides ≥ 5.1.7| kept     |
| CSS                      | Tailwind (vendored) + CSS variables | kept     |
| Light JS                 | htmx + reveal.js + KaTeX            | kept     |
| Deploy                   | actions/upload-pages-artifact + actions/deploy-pages | NEW |

Explicitly NOT using: pandoc, watchdog, livereload, ghp-import,
peaceiris-actions-gh-pages, sphinx, mkdocs.

---

## 14. Migration sequence

### Phase 0 — Plugin in place (in current repo, on `claude/setup-manim-installation-4p24R`)
1. Add `src/simplex/plugin.py::activate()`.
2. Register `[project.entry-points."manim.plugins"] simplex = "simplex.plugin:activate"` in `pyproject.toml`.
3. Update `deck/scaffold.py` + `decks/_template/` to emit `manim.cfg` with `plugins = simplex` + `save_sections = True`. Backfill into `decks/showcase/`.
4. Smoke-render showcase to confirm theme still applies via plugin.

### Phase 1 — BaseSlide + hierarchy + chrome + exits
5. `engine/section_types.py::SimplexSectionType`.
6. Rewrite `slides/base.py`: drop env-var shim, add `next_slide` override, delegate `clear_scene`.
7. Rewrite `engine/animations.py`: `DEFAULT_EXITS` registry + `register_exit` + `exit_for` + free `clear_scene` + new `Remove`.
8. Delete `slides/content.py`. Add `slides/chrome.py::make_chrome`. Migrate showcase scenes.
9. Add `theme/tokens.py::WebPalette`. Add `theme/web_css.py::render_web_css`.
10. Migrate showcase: bare `next_slide()` for sub, `next_slide(name="...")` for main.

### Phase 2 — Render + web + CLI
11. Drop env vars from `render/runner.py`; add `--save_sections`. Stays subprocess.
12. Write `render/reconcile.py` reading native section JSON. Delete `render/manifest.py`.
13. Rewrite `render/html.py` using `manim_slides.convert.RevealJS`. Delete `_copy_segments`.
14. Rewrite `render/pdf.py` using `manim_slides.convert.PDF`. Add `render/pptx.py`.
15. Delete `render/cache.py` + callers. Drop `--force` and `simplex thumbs`.
16. New thumbnail rule (last frame of `sub[thumbnail_section_index]`).
17. Wire web palette CSS injection in `web/builder.py` + `render/html.py`.
18. Add `DeckConfig.{caching,self_test,render_quality_*,slides,slide_order,web}`.
19. Add `simplex test` + `simplex serve --watch`.

### Phase 3 — Three-repo split (USER must create repos first)
20. Create `simplex-core` repo on GitHub. Move `src/simplex/{plugin,section_types,engine,theme,slides}` there. Wire `manim-simplex` entry-point. Tag `v0.2.0-rc1`.
21. In `simplex`, remove moved dirs; depend on `manim-simplex>=0.2.0rc1`. Verify PEP 420 namespace.
22. Tag `simplex` `v0.2.0-rc1`. Verify install via fresh venv.
23. Create `simplex-lectures-template` repo. Add deploy.yml + example deck. Mark as GitHub Template.
24. Add `simplex init` CLI command.
25. End-to-end smoke: gh repo create → uv sync → simplex new → edit → simplex serve --watch → push → Pages publishes.
26. Tag all three `v0.2.0`. Publish to PyPI.

### Phase 4 — Hardening
27. `simplex-core` CI: pytest + plugin activate smoke.
28. `simplex` CI: render-smoke over showcase via `simplex test`.
29. Lectures template: no CI of its own; consumers run their own `deploy.yml`.

---

## 15. Files: critical paths

**New**
- `src/simplex/plugin.py`
- `src/simplex/engine/section_types.py`
- `src/simplex/slides/chrome.py`
- `src/simplex/theme/web_css.py`
- `src/simplex/render/reconcile.py`  (replaces `manifest.py`)
- `src/simplex/render/pptx.py`

**Rewritten**
- `src/simplex/slides/base.py`         (drops env-var shim + next_slide override)
- `src/simplex/engine/animations.py`   (default-exit registry)
- `src/simplex/render/runner.py`       (drops env vars, adds --save_sections)
- `src/simplex/render/html.py`         (in-process via manim_slides.convert)
- `src/simplex/render/pdf.py`          (in-process)
- `src/simplex/render/thumbnail.py`    (new "second-to-last sub" rule)
- `src/simplex/web/builder.py`         (drops cache; uses reconcile; palette CSS)
- `src/simplex/cli/commands.py`        (adds test/--watch/init; drops --force/thumbs)
- `src/simplex/deck/config.py`         (adds SlideOverride, WebOverride, new fields)
- `src/simplex/deck/scaffold.py`       (emits manim.cfg)
- `src/simplex/theme/tokens.py`        (adds WebPalette)
- `src/simplex/theme/presets.py`       (fills WebPalette)

**Deleted**
- `src/simplex/slides/content.py`
- `src/simplex/render/cache.py`
- `src/simplex/render/manifest.py`

**Updated config**
- `pyproject.toml`            — entry-point, watchfiles dep
- `ruff.toml`                 — decks/** per-file-ignores
- `decks/showcase/manim.cfg`  — NEW
- `decks/_template/manim.cfg` — NEW
- `decks/showcase/slides/scenes.py` — migrated to new APIs
- `.github/workflows/publish.yml` → rename to `deploy.yml`, use actions/deploy-pages

---

## 16. Verification

Each phase is independently revertible. Verification steps:

- **Phase 0 done** when smoke-rendering `decks/showcase/` produces
  `media/videos/showcase/.../sections/<Scene>.json` files.
- **Phase 1 done** when `decks/showcase/slides/scenes.py::TextHelpers`
  uses `self.next_slide(name="Intro")` and the section JSON's `"type"`
  field reads `"simplex.main"`.
- **Phase 2 done** when re-editing one animation in `scenes.py` and
  running `simplex render showcase` re-encodes only that animation
  (manim logs `using cached data for …` for everything else).
- **Phase 3 done** when `gh repo create my-lectures --template
  shlomi-perles/simplex-lectures-template`, `uv sync`, `simplex new
  ml/test`, `simplex build` produces a working `site/`.
- **Phase 4 done** when CI is green on both `simplex-core` and `simplex`.

---

## 17. Open verification items (during implementation)

- `section_type` string round-trips through `Slide.next_slide(
  section_type=...) → Scene.next_section → Section(type_=) → JSON
  "type"`. One `print(sec["type"])` on first integration confirms.
- `manim_slides.convert.RevealJS` accepts a way to inject custom CSS
  (either via `template=Path(...)` or a `data: dict` template-context
  slot). Fall back to a post-processing regex insert if neither works.
- PEP 420 namespace packages: confirm `hatchling`'s wheel does not
  inject `simplex/__init__.py`. If it does, switch to setuptools with
  `find_namespace_packages`.
- `Unwrite`, `ShrinkToCenter`, `Uncreate`, `FadeOut` all accept a single
  mobject and don't choke on `VGroup`. If `Unwrite` fails on non-`Tex`
  subclasses, restrict the registry to exact-type matches.
- `actions/deploy-pages@v4` requires repo Pages source set to "GitHub
  Actions" (not a branch). Template README must call this out.
- `watchfiles.awatch` debounces by default (~100ms). Confirm SSE doesn't
  spam the browser on bulk saves.
