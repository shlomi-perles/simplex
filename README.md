# Simplex

[![PyPI version](https://img.shields.io/pypi/v/simplex-web.svg)](https://pypi.org/project/simplex-web/)
[![Python](https://img.shields.io/pypi/pyversions/simplex-web.svg)](https://pypi.org/project/simplex-web/)
[![CI](https://github.com/shlomi-perles/simplex/actions/workflows/ci.yml/badge.svg)](https://github.com/shlomi-perles/simplex/actions/workflows/ci.yml)
[![License](https://img.shields.io/pypi/l/simplex-web.svg)](https://github.com/shlomi-perles/simplex/blob/main/LICENSE)

Simplex is a Manim presentation workflow with a generated static web portal.
Write normal Manim scenes, mark slide boundaries with `manim-slides`, and let
Simplex render the deck, reconcile slide metadata, build thumbnails, render
notes, and publish a browsable site.

The PyPI distribution is `simplex-web`. It installs the `simplex` command and
imports into the `simplex.*` namespace.

## Why Simplex?

- Author scenes with standard Manim objects such as `MathTex`, `VGroup`,
  `Axes`, and `Animation`.
- Use `manim-simplex` slide bases, layout regions, theme tokens, and mobjects.
- Organize decks under `decks/` with a small `deck.toml`.
- Build a static portal with deck pages, notes, citations, math rendering,
  thumbnails, RevealJS playback, title-based PDF downloads, and optional live reload.
- Keep the rendered video frames clean; navigation chrome lives in the web
  viewer where it can be changed without re-rendering videos.

## Packages

Simplex is split into a small toolkit:

| Repository | PyPI | Purpose |
|---|---|---|
| [`manim-simplex`](https://github.com/shlomi-perles/manim-simplex) | `manim-simplex` | Manim plugin, themes, slide bases, mobjects, and manifest schema. |
| [`simplex`](https://github.com/shlomi-perles/simplex) | `simplex-web` | CLI, deck discovery, render orchestration, static portal builder. |
| [`simplex-lectures-template`](https://github.com/shlomi-perles/simplex-lectures-template) | - | Starter lectures repository. |

The import namespace is still `simplex`. `manim-simplex` provides the top-level
authoring facade (`from simplex import BaseSlide, Caption`), while
`simplex-web` contributes CLI and site-builder modules such as `simplex.web`.

## Requirements

- Python 3.13 or newer
- FFmpeg
- A LaTeX distribution
- Manim's native dependencies, including Cairo and Pango on Linux

Typical system packages:

```bash
# Ubuntu / Debian
sudo apt-get install texlive-latex-extra texlive-fonts-recommended ffmpeg \
                     libcairo2-dev libpango1.0-dev
```

```powershell
# Windows
winget install MiKTeX.MiKTeX
winget install Gyan.FFmpeg
```

After installation, run:

```bash
simplex doctor
```

## Install

```bash
pip install simplex-web
```

With `uv`:

```bash
uv add simplex-web
```

For local development in this repository:

```bash
uv sync
uv run simplex doctor
```

## Quick Start

Create a new deck in an existing project:

```bash
simplex new algorithms/hash-tables
simplex render hash-tables
simplex build
simplex serve
```

Then open:

```text
http://localhost:8000
```

To start from the GitHub template instead:

```bash
simplex init my-lectures
cd my-lectures
simplex new first-deck
simplex build
simplex serve
```

## Deck Layout

`simplex new hash-tables` creates a deck like this:

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

[slides."Key Idea"]
notes_anchor = "key-idea"
```

`entrypoints` points to scene classes inside the deck directory. Legacy
`scenes = ["Intro"]` is still accepted for single-file `slides.py` decks, but
`entrypoints` is the preferred layout.

## Authoring Slides

A scene is ordinary Manim plus the Simplex slide base:

```python
from manim import DOWN, ORIGIN, Tex, Write

from simplex import BaseSlide, get_active_theme


class Intro(BaseSlide):
    def construct(self) -> None:
        theme = get_active_theme()

        title = Tex("Hello, Simplex", font_size=theme.typography.h1)
        self.region.place(title, ORIGIN)

        subtitle = Tex(r"$e^{i\pi} + 1 = 0$", font_size=theme.typography.h2)
        subtitle.next_to(title, DOWN, buff=0.4)

        self.play(Write(title), Write(subtitle))
        self.next_slide()
```

`BaseSlide` comes from `manim-simplex`. It provides the default theme,
bounded layout region, slide lifecycle helpers, and section metadata used by
the web builder.

## Notes And Site

Each deck can include `notes.md`. The site builder renders Markdown notes,
inline math, display math, citations from `refs.bib`, and slide references.
Prefer label-based slide refs such as `[slide:key-idea]`; numeric refs still
work for quick drafts. When a TeX engine is available, builds also emit
`<title>-note.pdf` for the deck download menu.

Theorem-style notes use Markdown blockquotes with TeX labels. Write
`> **Theorem.** \label{thm:first}` and reference it with `\ref{thm:first}`
or `\autoref{thm:first}`; the web preview numbers it automatically and the
notes PDF emits matching `amsthm` environments.

Site-wide options live in `site.toml`:

```toml
brand = "Simplex"
tagline = "Manim presentations, rendered."

nav = [
  { label = "Decks", href = "/" },
  { label = "GitHub", href = "https://github.com/shlomi-perles/simplex" },
]
```

Links labeled `GitHub` are shown as the footer GitHub icon, next to the
`Built with Simplex` mark.

Deployment-only settings are read from environment variables:

- `SIMPLEX_BASE_URL`
- `SIMPLEX_GA_TAG`
- `SIMPLEX_BRAND`
- `SIMPLEX_PREVIEW`

## CLI

| Command | Purpose |
|---|---|
| `simplex new <slug>` | Create `decks/<slug>/` from the bundled template. |
| `simplex new <section>/<slug>` | Create a deck inside a named section. |
| `simplex init [dir]` | Create a lectures repo from the GitHub template. |
| `simplex render <slug>` | Render one deck into `site/decks/<slug>/`. |
| `simplex render <slug>::<Scene>` | Render one scene from a deck. |
| `simplex build` | Render decks and build the static portal under `site/`. |
| `simplex build --no-render` | Rebuild portal HTML from existing render output. |
| `simplex serve [--watch]` | Serve `site/` locally, optionally with live reload. |
| `simplex test` | Smoke-render decks by rendering only the first animation. |
| `simplex clean` | Remove generated `site/` and `media/` output. |
| `simplex doctor` | Check required binaries on `PATH`. |

## Development

```bash
git clone https://github.com/shlomi-perles/simplex.git
cd simplex
uv sync
uv run ruff check .
uv run ruff format --check .
uv run basedpyright
uv run pytest -q
```

The release workflow uses GitHub Actions Trusted Publishing to upload
`simplex-web` to PyPI. No PyPI API token is stored in the repository.

## License

MIT.
