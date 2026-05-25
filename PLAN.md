# Simplex — Implementation Master Plan

## 1. Context

You currently maintain `dastimator/`, a Manim presentation library glued to the **deprecated** `manim-editor` package. It has no `pyproject.toml`, hardcoded paths in every builder, a 892-line hand-edited HTML portal (`docs/index.html`), and a workaround (`manim_editor_autocreated_scene_fix`) that exists purely to paper over upstream bugs in a dead project.

**Simplex** replaces that pipeline end-to-end. It keeps Dastimator's **visual identity** (color palette, math typography, compact LaTeX preamble) but rebuilds the engine on `manim-slides`, lets authors write **vanilla Manim code** (no wrappers, no factories), and adds a generated web portal so adding a deck becomes `simplex new` + `git push`.

**Locked-in choices:**
- Env / lockfile: **uv**. Python: **3.14+**, strict (no legacy).
- Web: **Python-generated static site** on **GitHub Pages**.
- Notes: **one `notes.md` per deck**, English-only.
- Package name: **`simplex`**.
- Authors write **vanilla Manim** (`MathTex(...)`, `VGroup(...).arrange(RIGHT)`); the framework configures defaults *behind* the API rather than wrapping it.
- Every directory ships a **<=50-line `README.md`**; only the repo root has a long README.

---

## 2. Architecture Proposal

### 2.1 Repository layout

```
simplex/
|-- README.md
|-- STYLE.md
|-- pyproject.toml
|-- uv.lock
|-- .python-version            # "3.14"
|-- .gitignore                 # __pycache__, .ruff_cache, .pytest_cache, .basedpyright,
|                              # media/, site/, .simplex_cache/, *.egg-info/
|-- ruff.toml
|-- .github/workflows/{ci.yml,publish.yml}
|-- scripts/{bootstrap.ps1,bootstrap.sh}
|-- src/simplex/
|   |-- __init__.py
|   |-- README.md
|   |-- theme/                 # design tokens (Pydantic, frozen)
|   |   |-- tokens.py          # Palette, Typography, Spacing, Motion, LatexProfile, Theme
|   |   |-- presets.py         # SIMPLEX_DARK = Theme(...), ACADEMIC_LIGHT = Theme(...)
|   |   `-- context.py         # ContextVar-backed active_theme() + get_active_theme()
|   |-- engine/                # small, additive helpers (no wrapping)
|   |   |-- defaults.py        # apply_theme_defaults(theme)
|   |   |-- config.py          # configure_manim(theme, quality_key)
|   |   |-- region.py          # Region: mutable active drawing area
|   |   `-- animations.py      # Remove(mob), set_exit_animation(mob, cls)
|   |-- slides/                # slide base classes (manim-slides)
|   |   |-- base.py            # BaseSlide(manim_slides.Slide)
|   |   |-- content.py         # ContentSlide
|   |   `-- components/        # higher-level domain mobjects
|   |       |-- graph.py       # Node, Edge
|   |       `-- array.py       # ArrayMob
|   |-- deck/                  # per-deck config + discovery
|   |   |-- config.py
|   |   |-- registry.py
|   |   `-- scaffold.py
|   |-- render/                # manim-slides invocation + cache
|   |   |-- runner.py
|   |   |-- pdf.py
|   |   `-- cache.py
|   |-- web/                   # static-site generator
|   |   |-- builder.py
|   |   |-- notes.py
|   |   |-- templates/         # Jinja2 (base, index, deck)
|   |   `-- static/            # vendored tailwind.min.css, katex/, htmx.min.js
|   `-- cli/
|       `-- commands.py        # new | render | serve | build | clean | doctor
|-- decks/
|   `-- _template/{deck.toml,slides.py,notes.md,assets/}
`-- tests/
```

### 2.2 Configuration management

Two layers separated by lifetime:

- **Theme tokens** -- `pydantic.BaseModel` with `model_config = ConfigDict(frozen=True)` in `theme/tokens.py`. Type-safe, immutable, hashable. Initial values seeded from `dastimator/source/tools/consts.py:1-62`. Presets are **instances** (not subclasses) -> runtime-swappable via `with active_theme(ACADEMIC_LIGHT):`.
- **Deck config** -- `deck.toml` -> `DeckConfig(BaseModel)` with validators for slug (kebab-case, URL-safe), title, summary, tags, theme name, scene render order, optional voiceover flag.

Slide bases pull the active theme in `setup()` via a `ContextVar`.

### 2.3 LaTeX / TeX environment handling

| Concern | Dastimator source | Simplex home |
|---|---|---|
| Global preamble (compact math display, custom commands) | `REMOVE_MATH_SPACE_PREAMBLE` (`consts.py:54-58`) | `theme.latex.preamble: str` -> injected into the theme's `TexTemplate` |
| Per-use environment (e.g. `{minipage}{20cm}`) | `DEFINITION_TEX_ENV` (`consts.py:53`) | `theme.latex.environments: dict[str, str]` |
| Math/text colors, font sizes | scattered across `consts.py` | `theme.palette` + `theme.typography`; applied via `Tex.set_default(...)` |

`engine/defaults.py::apply_theme_defaults(theme)` calls `Tex.set_default(...)`, `MathTex.set_default(...)`, `Text.set_default(...)`, `Line.set_default(...)`, etc. so a deck author writes plain `MathTex(r"\frac{1}{2}")` and gets theme colors + preamble for free.

### 2.4 Manim integration philosophy

**No anti-corruption wall.** Authors and the framework `from manim import ...` directly. Engine surface is **additive convenience** -- never replaces vanilla Manim:

- `engine/config.py::configure_manim(theme, quality_key)` -- mutates `manim.config` once. No custom `QualityProfile` enum -- Manim already ships `QUALITIES`.
- `engine/defaults.py::apply_theme_defaults(theme)` -- calls `Mobject.set_default(...)`.
- `engine/region.py::Region` -- see 2.5.
- `engine/animations.py` -- `Remove`, `set_exit_animation`.
- `slides/base.py::BaseSlide.clear_scene(exclude=...)`.

We deliberately do NOT ship: factories like `math(...)` / `title(...)`, layout managers like `VStack` / `HStack` / `Grid` (`VGroup(*items).arrange(direction)` is already one line), nor a custom quality enum.

### 2.5 Active region (replaces "safe zone")

A `Region` is a **mutable** rectangular sub-area of the frame, owned by `BaseSlide` as `self.region`. Authors place Mobjects relative to it and resize it during the scene. `ContentSlide.setup` calls `self.region.shrink(top=header_h, bottom=footer_h)` so its body never overlaps the chrome.

### 2.6 Exit animations & `clear_scene`

`Remove(mob)` looks up `mob._simplex_exit` (a per-instance attribute set via `set_exit_animation`), falling back to `FadeOut`. `BaseSlide.clear_scene(exclude=())` plays `Remove` for every mobject not in `exclude`.

### 2.7 BaseSlide shape

`BaseSlide(manim_slides.Slide)` -- in `setup()` it pushes the active theme, runs `configure_manim` + `apply_theme_defaults`, and seeds `self.region = Region.full_frame()`. `tear_down()` pops the theme context.

### 2.8 Web portal generation

`simplex build` runs five stages: discover decks, render via manim-slides, export PDFs, render notes.md -> HTML with KaTeX, write `site/` via Jinja2.

### 2.9 Dependency & environment management

`uv` owns Python toolchain + lockfile. System deps (LaTeX/ffmpeg/Cairo/Pango) sit outside `uv`. `simplex doctor` verifies each binary on PATH.

### 2.10 Modern Python tooling stack

| Concern | Library |
|---|---|
| Env + lockfile + Python toolchain | uv |
| Config validation | pydantic v2 |
| Layered settings | pydantic-settings |
| TOML read / write | tomllib / tomli-w |
| CLI | typer |
| Terminal UX | rich |
| Logging | structlog |
| Lint + format | ruff |
| Type checking | basedpyright --strict |
| Tests + snapshots | pytest, pytest-xdist, syrupy |
| Markdown -> HTML | markdown-it-py + mdit-py-plugins |
| Math (client) | KaTeX (vendored) |
| Templating | jinja2 |
| Syntax highlight | pygments |
| Render engine | manim, manim-slides |
| CSS | Tailwind (vendored CDN build) |
| Light JS | htmx (vendored) |

### 2.11 Python 3.14+ style (enforced in `STYLE.md`)

- PEP 695 generics: `class Box[T]:`, `type Vec = list[float]`. No `TypeVar()`.
- Built-in generics + `X | None`; no `typing.Optional` / `typing.List`.
- No `from __future__` imports.
- `pathlib.Path` everywhere; ruff bans `os.path`.
- Pydantic v2 at every IO boundary; no bare `dict[str, Any]`.
- f-strings; **t-strings** (PEP 750) for any user-influenced string flowing to subprocess args, HTML, or shells.
- `match`/`case` over discriminating `if/elif` chains.
- `basedpyright --strict` clean.
- Files >300 lines need a justification comment.

### 2.12 Per-directory micro-documentation

Every directory under `src/simplex/`, `decks/`, and `tests/` ships a `README.md` <=50 lines answering: **Scope**, **Public surface**, **Don't**. Enforced by `tools/check_readmes.py`.

---

## 3. Master Task List

1. Repo skeleton & tooling (`pyproject.toml`, `uv.lock`, ruff/basedpyright config, `.gitignore`, bootstrap scripts, `simplex doctor` stub).
2. `STYLE.md` + per-dir README enforcement.
3. Theme tokens (`theme/tokens.py`, `theme/presets.py`, `theme/context.py`) seeded from `dastimator/source/tools/consts.py:1-62`.
4. Engine `defaults.py` + `config.py`.
5. Engine `region.py`.
6. Engine `animations.py`.
7. Slide bases on manim-slides (`base.py`, `title.py`, `content.py`, `section.py`).
8. Domain components (`graph.py`, `array.py`).
9. Deck config & scaffold + `decks/_template/`.
10. Render pipeline (`runner.py`, `pdf.py`, `cache.py`).
11. Notes renderer (markdown-it-py + dollarmath, KaTeX vendored).
12. Static portal (Jinja templates, Tailwind/htmx vendored, builder).
13. CLI (`new | render | build | serve | clean | doctor`).
14. CI & deployment workflows.
15. Migrate one Dastimator topic (BST or Hash Tables) end-to-end.

## 4. Critical files

**Port (read, redesign -- do not copy):**
- `dastimator/source/tools/consts.py:1-62` -> seeds `theme/presets.py:SIMPLEX_DARK`.
- `dastimator/source/tools/graphs/{node,edge}.py` -> `slides/components/graph.py`.
- `dastimator/source/tools/array.py` -> `slides/components/array.py`.
- `dastimator/source/tools/funcs.py` -> split into `engine/animations.py` and helper functions.

**Do NOT inherit:** anything from `manim_editor`, `dastimator/docs/index.html`, any vendored mp4/image/css/js from `dastimator/docs/`.

## 5. Verification

- Step 1: `uv sync && uv run simplex doctor` exits 0 on a clean Windows box.
- Step 2: pre-commit fails when any directory under `src/simplex/` lacks a README or exceeds 50 lines.
- Step 3: `SIMPLEX_DARK.palette.background == "#242424"`, `theme.latex.environments["definition"] == "{minipage}{20cm}"`, models frozen.
- Step 4: After `apply_theme_defaults`, a vanilla `MathTex(r"x")` has theme color and preamble.
- Step 5: `Region.full_frame().shrink(top=0.5).center` returns the expected coordinate.
- Step 6: `Remove(mob)` -> `FadeOut` by default; `set_exit_animation(mob, ShrinkToCenter)` -> `ShrinkToCenter`.
- Step 7: `simplex render _template` produces non-empty manim-slides HTML.
- Step 9-10: `simplex new demo && simplex render demo` works; second run hits cache.
- Step 11: notes `$E=mc^2$` -> KaTeX-classed HTML.
- Step 12-13: `simplex build && simplex serve` opens a deck portal.
- Step 14: pushing to `main` deploys to Pages with the new deck card.
