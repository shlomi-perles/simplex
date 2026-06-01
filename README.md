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
- a deck manifest schema and render reconciliation pipeline;
- the `simplex` CLI for deck scaffolding, rendering, site building, serving,
  testing, and diagnostics;
- a static lecture portal with notes, citations, math rendering, thumbnails,
  RevealJS playback, and GitHub Pages-friendly output.

The CLI and plugin intentionally live in one distribution so consumers only
depend on `manim-simplex`.

## Requirements

- Python 3.13+
- Manim Community 0.20.1+
- manim-slides 5.1.7+
- FFmpeg, Cairo, Pango, and a TeX distribution when rendering TeX. See the
  Manim installation guide: https://docs.manim.community/en/stable/installation.html

Typical system packages:

```bash
sudo apt-get install texlive-latex-extra texlive-fonts-recommended ffmpeg \
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

Enable the plugin in the `manim.cfg` next to your scenes or deck:

```ini
[CLI]
plugins = simplex
save_sections = True
```

Manim imports `simplex.plugin` through the `manim.plugins` entry point. The
plugin applies the active Simplex theme to Manim defaults, registers Pygments
styles, sets the TeX template, sets the background color, and enables section
JSON output.

## Quick Start

```python
from manim import ORIGIN, MathTex, Write

from simplex import Slide


class HelloSlide(Slide):
    def setup(self) -> None:
        super().setup()
        self.setup_chrome(header="Hello, Simplex")

    def construct(self) -> None:
        eq = MathTex(r"e^{i\pi} + 1 = 0")
        self.region.place(eq, ORIGIN)
        self.play(Write(eq))
        self.next_slide()
```

Render as a slide deck:

```bash
uv run manim-slides render path/to/scene.py HelloSlide
uv run manim-slides present HelloSlide
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
| `simplex.slides` | `Slide`, `ThreeDSlide`, `OutlineScene`, `OutlinePart`, `Chrome`, `make_chrome`. |
| `simplex.engine` | `Region`, `ExitAnim`, `clear_scene`, `exit_for`, `register_exit`, `set_exit_animation`, `HighlightResult`, `apply_theme_defaults`. |
| `simplex.mobjects` | `Node`, `Edge`, `ArrayMob`, `ArrayEntry`, `ArrayPointer`, `OutlineProgressBar`, `Paper`, `ShowPaper`, `DismissPaper`, `PickPage`. |
| `simplex.theme` | `Theme`, `Palette`, `Typography`, `Spacing`, `Motion`, `LatexProfile`, `WebPalette`, `active_theme`, `get_active_theme`, `presets`, `render_web_css`. |
| `simplex.manifest` | `DeckManifest`, `MainSlide`, `Subsection`, the manifest schema written by the render pipeline. |
| `simplex.deck` | `DeckConfig`, `discover`, `scaffold`, section metadata, bundled deck template. |
| `simplex.render` | Manim runner, manifest reconciliation, thumbnails, HTML, PDF, PPTX, notes PDF, filenames. |
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
| `simplex build` | Render decks and build the static portal under `site/`. |
| `simplex build --no-render` | Rebuild portal HTML from existing render output. |
| `simplex build --slide-theme dark` | Build only one true slide theme (`dark` or `light`) for faster tests. |
| `simplex serve [--watch]` | Serve `site/` locally, optionally with live reload. |
| `simplex test --slide-theme dark` | Smoke-render decks by rendering only the first animation. |
| `simplex clean` | Remove generated `site/` and `media/` output. |
| `simplex doctor` | Check required binaries on `PATH`. |

## Deck Layout

`simplex new hash-tables` creates:

```text
decks/hash-tables/
|-- deck.toml
|-- manim.cfg
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
theme = "simplex_dark"
quality = "high_quality"
entrypoints = ["slides.intro:Intro", "slides.intro:KeyIdea"]

[slide_themes]
enabled = true
dark = "simplex_dark"
light = "simplex_light"
default = "dark"

[slides."Key Idea"]
notes_anchor = "key-idea"
```

`[slide_themes] enabled = true` renders real dark and light slide videos,
thumbnail images, and slide HTML into isolated `themes/dark/` and
`themes/light/` folders. The deck player swaps between those compiled
artifacts when the slide-theme toggle changes, so light mode is not a CSS
filter over dark pixels. The package defaults are `simplex_dark` and
`simplex_light`; set `[slide_themes] enabled = false` in `site.toml` or a
deck's `deck.toml` to keep the legacy single render plus filter toggle. Deck
settings override site settings.

During local iteration or CI smoke tests, render one true variant:

```bash
uv run simplex build --slide-theme dark
uv run simplex render hash-tables --slide-theme light
uv run simplex test --slide-theme dark
```

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
