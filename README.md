# Simplex

[![PyPI version](https://img.shields.io/pypi/v/manim-simplex.svg)](https://pypi.org/project/manim-simplex/)
[![Python](https://img.shields.io/pypi/pyversions/manim-simplex.svg)](https://pypi.org/project/manim-simplex/)
[![CI](https://github.com/shlomi-perles/simplex/actions/workflows/ci.yml/badge.svg)](https://github.com/shlomi-perles/simplex/actions/workflows/ci.yml)
[![License](https://img.shields.io/github/license/shlomi-perles/simplex.svg)](https://github.com/shlomi-perles/simplex/blob/main/LICENSE)

Simplex is a toolkit for Manim lecture projects. The repository is named
`simplex`, and the PyPI distribution is named `manim-simplex` because the bare
`simplex` package name is already taken on PyPI. It ships one Python package
namespace, `simplex`, with:

- a Manim plugin (`plugins = simplex`);
- theme tokens, mobjects, layout regions, slide bases, and animation helpers;
- a timeline manifest schema and render/package pipeline;
- the `simplex` CLI for deck scaffolding, rendering, site building, serving,
  testing, and diagnostics;
- a static lecture portal with notes, citations, math rendering, thumbnails,
  Shaka-backed HLS playback, MP4 fallback, and GitHub Pages-friendly output.

The CLI and plugin intentionally live in one distribution so consumers only
depend on `manim-simplex`.

## Playback Architecture

Simplex uses a continuous timeline player: render scene units independently,
compose one lecture timeline per theme, package HLS/CMAF plus MP4 fallback,
and navigate by seeking to cue timestamps instead of swapping per-slide videos.

## Requirements

- Python 3.13+
- Manim Community 0.20.1+
- Cairo, Pango, and a TeX distribution when rendering TeX. FFmpeg is optional
  as a packaging fallback. See the
  Manim installation guide: https://docs.manim.community/en/stable/installation.html

Typical system packages:

```bash
sudo apt-get install texlive-latex-extra texlive-fonts-recommended texlive-science \
                     libcairo2-dev libpango1.0-dev
```

```powershell
winget install MiKTeX.MiKTeX
winget install Gyan.FFmpeg
```

## Install

```bash
pip install manim-simplex
```

With uv:

```bash
uv add manim-simplex
```

Verify that Manim can discover the plugin:

```bash
python -m manim plugins -l
```

The output should include `simplex`.

## Configure Manim

Enable the plugin in a project-level `manim.cfg`:

```ini
[CLI]
plugins = simplex
quality = high_quality
```

Manim imports `simplex.plugin` through the `manim.plugins` entry point. The
plugin applies the active Simplex theme to Manim defaults, registers Pygments
styles, sets the TeX template, and sets the background color. Simplex records
cue timing directly from `Scene.time`; Manim section output remains at Manim's
default unless you explicitly enable it for debugging.

When rendering a Simplex deck, the runner looks for `manim.cfg` in the lecture
project root and also in the deck directory. If both exist, Simplex passes
Manim a temporary merged config: deck-local fields override matching global
fields, and unrelated fields are preserved. Command-line Manim flags still win
for one-off renders.

## Quick Start

```python
from manim import ORIGIN, MathTex, Write

from simplex import SimplexScene


class HelloSlide(SimplexScene):
    def setup(self) -> None:
        super().setup()
        self.setup_chrome(header="Hello, Simplex")

    def construct(self) -> None:
        self.slide(title="Hello, Simplex")
        eq = MathTex(r"e^{i\pi} + 1 = 0")
        self.region.place(eq, ORIGIN)
        self.play(Write(eq))
```

Render a standalone scene:

```bash
uv run manim -pql path/to/scene.py HelloSlide
```

Or create a lecture-site deck and build the portal:

```bash
uv run simplex new algorithms/hash-tables
uv run simplex render hash-tables
uv run simplex build
uv run simplex serve
```

## Public Surface

| Module | Public surface |
| --- | --- |
| `simplex.plugin` | `activate()` entry point used by Manim. |
| `simplex.slides` | `SimplexScene`, `SimplexThreeDScene`, `Slide`, `ThreeDSlide`, `OutlineScene`, `OutlinePart`, `Chrome`, `make_chrome`. |
| `simplex.engine` | `Region`, `ExitAnim`, `clear_scene`, `exit_for`, `register_exit`, `set_exit_animation`, `HighlightResult`, `apply_theme_defaults`. |
| `simplex.mobjects` | `Node`, `Edge`, `ArrayMob`, `ArrayEntry`, `ArrayPointer`, `OutlineProgressBar`, `Paper`, `ShowPaper`, `DismissPaper`, `PickPage`, `Sphere`, `OpenGLSphere`, `ScalarFieldSurface`, `ColorBar`. |
| `simplex.theme` | `Theme`, `Palette`, `Typography`, `Spacing`, `Motion`, `LatexProfile`, `WebPalette`, `active_theme`, `get_active_theme`, `presets`, `resolve_palette`, `available_palette_names`, `render_web_css`. |
| `simplex.manifest` | `DeckManifest`, `Cue`, `ThemeTimeline`, and the schema v2 playback contract. |
| `simplex.deck` | `DeckConfig`, `discover`, `scaffold`, section metadata, bundled deck template. |
| `simplex.render` | Manim runner, timeline composition, HLS/MP4 packaging, cue images, PDF, PPTX, notes PDF, filenames. |
| `simplex.web` | Portal builder, notes renderer, citations, refs, templates, static assets, live reload. |
| `simplex.cli` | Typer application installed as the `simplex` command. |

## CLI

| Command | Purpose |
| --- | --- |
| `simplex new <slug>` | Create `decks/<slug>/` from the bundled template. |
| `simplex new <section>/<slug>` | Create a deck inside a named section. |
| `simplex init [dir]` | Create a lectures repo from the GitHub template. |
| `simplex render <slug>` | Render one deck into `site/decks/<slug>/`. |
| `simplex render <slug>::<Scene>` | Render one scene from a deck. |
| `simplex render <slug> --slide-theme light` | Render only one true slide theme for a deck. |
| `simplex render <slug> --disable_caching` | Forward Manim render flags to Manim. |
| `simplex build` | Render decks and build the static portal under `site/`. |
| `simplex build --disable_caching` | Forward Manim render flags to every deck render. |
| `simplex build --no-render` | Rebuild portal HTML from existing render output. |
| `simplex build --slide-theme dark` | Build only one true slide theme (`dark` or `light`) for faster tests. |
| `simplex serve [--watch]` | Serve `site/` locally, auto-picking the next free port if 8000 is busy. |
| `simplex test --slide-theme dark` | Smoke-render decks by rendering only the first animation. |
| `simplex theme-studio` | Generate and open the palette/code-style editor. |
| `simplex clean` | Remove generated `site/` and `media/` output. |
| `simplex doctor` | Check required binaries, PyAV packaging, and optional fallbacks. |

## Deck Layout

`simplex new hash-tables` creates:

```text
decks/hash-tables/
|-- deck.toml
|-- notes.md
|-- refs.bib
|-- assets/
`-- slides/
    |-- __init__.py
    `-- intro.py
```

The important fields in `deck.toml` are:

```toml
slug = "hash-tables"
title = "Hash Tables"
summary = "A one-line deck summary."
date = "2026-05-19"
entrypoints = ["slides.intro:Intro", "slides.intro:KeyIdea"]

[slide_themes]
enabled = true
dark = "simplex_dark"
light = "simplex_light"
default = "dark"

[web]
show_notes_date = true
```

Default Manim render settings live in the project-level `manim.cfg`.
Deck-local `manim.cfg` files are optional overrides; matching deck-local
fields override the global value for that deck, and unrelated fields are
merged. One-off render overrides can be passed through `simplex render` or
`simplex build`.
`simplex build --no-render` rejects Manim render flags because there is no
render subprocess to receive them.

The `date` field is optional. When omitted, Simplex tries to show the first
Git commit that added the deck. If that is unavailable, it falls back to the
last time the deck's slide structure changed, then the last changed Python
scene file. Set `[web] show_notes_date = true` to display the same resolved
date under the first notes heading and in the generated notes PDF.

Slide refs in `notes.md` are generated from the visible slide title. A slide
titled `Key Idea` is referenced as `[slide:key-idea]`; no `deck.toml` anchor
field is needed.

`voiceover` is not a Simplex deck setting or a Manim core `manim.cfg` field.
Use the separate `manim-voiceover` plugin from scene code when a deck needs
narration.

`[slide_themes] enabled = true` renders real dark and light slide videos,
thumbnail images, and slide HTML into isolated `themes/dark/` and
`themes/light/` folders. The deck player swaps between those compiled
artifacts when the slide-theme toggle changes, so light mode is not a CSS
filter over dark pixels. The package defaults are `simplex_dark` and
`simplex_light`; set `[slide_themes] enabled = false` in `site.toml` or a
deck's `deck.toml` to keep the legacy single render plus filter toggle. Deck
settings override site settings.

The top-level `theme = "..."` field is intentionally omitted from new decks.
It is only a single-render fallback for projects that disable true slide
themes. With `[slide_themes] enabled = true`, rendered slide pixels come from
the `dark` and `light` theme names below.

During local iteration or CI smoke tests, render one true variant:

```bash
uv run simplex build --slide-theme dark
uv run simplex render hash-tables --slide-theme light
uv run simplex test --slide-theme dark
```

## Code And Pseudocode

Simplex keeps Manim's native `Code` object as the authoring surface and adds a
few factories in `simplex.engine.code`:

```python
from simplex import code_block, code_with_math, highlight_code_lines, pseudocode_block

code = code_block("def f(x):\n    return x + 1")
algorithm = pseudocode_block(
    r"""
\SetKwInput{Input}{Input}
\Input{Value $n$}
Initialize $s\leftarrow 0$\;
Return $s$\;
""",
    caption=r"\textbf{Running Sum}",
)
```

`pseudocode_block(...)` compiles an `algorithm2e` algorithm with the shared
Simplex TeX template and returns a `Code` instance. Its `code_lines` are the
rendered, algorithm2e-numbered rows, so `highlight_code_lines(algorithm, [2])`
and `code_explain(...)` target the visible algorithm line numbers. Use
`code_block(..., pseudocode=True)` for the same renderer when you prefer one
factory. On TeX Live systems, install `texlive-science` for `algorithm2e.sty`.

## Themes And Palettes

Theme names come from built-ins (`simplex_dark`, `simplex_light`) or JSON files
in `simplex_themes/themes/`. Configure them globally in `site.toml`:

```toml
[slide_themes]
enabled = true
dark = "simplex_dark"
light = "my_light"
default = "dark"
```

Deck `deck.toml` files may include their own `[slide_themes]` block when one
deck needs different themes. Deck settings override `site.toml`.

Theme JSON files can declare `manim_palette = "..."`. Simplex resolves that
palette before scene imports, patches Manim color constants such as `BLUE`,
`BLUE_A`, `WHITE`, and `GRAY`, then derives any missing Simplex semantic colors
from it. Explicit theme `palette` fields still win. `simplex_dark` keeps
Manim's default palette, while `simplex_light` uses the built-in
`simplex_light` palette.

Example `simplex_themes/themes/my_light.json`:

```json
{
  "manim_palette": "simplex_light",
  "code_style": "simplex_solarized_light",
  "palette": {
    "background": "#EEEAD8",
    "font": "#3C313F",
    "vertex": "#355561",
    "vertex_stroke": "#426A79"
  },
  "web_palette": {
    "surface": "#F8F2DD",
    "text_muted": "#756E63"
  }
}
```

`palette` controls rendered Manim slide pixels: `background`, `font`,
`accent`, `vertex`, `vertex_stroke`, `edge`, `weight`, `visited`, `label`, and
`distance`. Missing fields are derived from `manim_palette`; if
`manim_palette` is omitted, missing fields derive from Manim defaults.
Custom palette fields are preserved on `get_active_theme().palette`, so
scene code can use project-specific semantic colors:

```json
{
  "palette": {
    "warning": "#FFD166",
    "success": "#2A9D8F"
  }
}
```

Fields can also hold both true-theme values in one place:

```json
{
  "palette": {
    "warning": { "light": "#775500", "dark": "#FFD166" },
    "background": { "light": "#F7F1DF", "dark": "#111827" }
  }
}
```

Simplex resolves those objects from the actual render role (`dark` or
`light`), not from the theme file name. This allows `dark = "lecture"` and
`light = "lecture"` to share one JSON file when that is clearer.

`code_style` controls Manim slide `Code` objects for that theme. It accepts a
Simplex style, a Pygments style name, or a custom style exported into
`simplex_themes/code_styles/`.

`web_palette` controls generated HTML/player shell colors. Decks can still
override those shell colors with `[web] background`, `[web] text_primary`,
`[web] accent`, etc. Markdown notes code blocks are separate and default to
`SimplexSolarizedLight`; override them per deck with:

```toml
[web]
notes_code_style = "simplex_pycharm"
```

Create or compare palettes and code styles with:

```bash
uv run simplex theme-studio
```

In lecture repos, put Theme Studio code-style exports in
`simplex_themes/code_styles/`, palette `.json` or `.itermcolors` exports in
`simplex_themes/palette_styles/`, and complete theme JSON files in
`simplex_themes/themes/`.

Append `@opengl` to one entrypoint when a scene should render with ManimCE's
OpenGL renderer:

```toml
entrypoints = ["slides.intro:Intro", "slides.surface:SurfaceColoring@opengl"]
```

## Development

```bash
git clone https://github.com/shlomi-perles/simplex.git
cd simplex
uv sync --all-extras
uv run playwright install chromium
uv run pre-commit install
```

Useful checks:

```bash
python tools/check_readmes.py
uv run ruff check .
uv run ruff format --check .
uv run basedpyright
uv run pytest -q
uv run pytest tests/web/test_player_browser.py -q
uv run python tools/vendor_web_assets.py
uv build --no-sources
uvx twine check dist/*
```

Run smoke tests locally:

```bash
uv run python -c "import simplex.plugin; simplex.plugin.activate(); print('ok')"
uv run manim plugins -l
uv run simplex --help
uv run simplex test --only showcase
```

## Release

Releases are automated through Release Please and PyPI Trusted Publishing.
Commit changes using Conventional Commits (`feat:`, `fix:`, `chore:`). When
changes land on `main`, Release Please opens or updates a release PR. Merging
that PR creates the GitHub release, builds the package with uv, publishes
`manim-simplex` to PyPI via OIDC, and dispatches a template update workflow.

Manual version bumps and chained `simplex-web` releases are no longer part of
the release process.

## License

MIT. See [LICENSE](LICENSE).
