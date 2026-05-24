# Simplex

A Manim-slides presentation framework with a generated web portal.

Authors write **vanilla Manim** (`MathTex(...)`, `VGroup(...).arrange(RIGHT)`); Simplex configures defaults underneath via frozen theme tokens. A `simplex new` command scaffolds a new deck; `simplex build` renders every deck and produces a static portal for GitHub Pages.

## The three repos

`simplex` is one of three packages that together make up the v0.2.0 toolkit:

| Repo | PyPI | Role |
|---|---|---|
| [`manim-simplex`](https://github.com/shlomi-perles/manim-simplex) | `manim-simplex` | The manim plugin: mobjects, theme, `BaseSlide`, the `manim.plugins` entry-point. |
| [`simplex`](https://github.com/shlomi-perles/simplex) | `simplex-web` | The platform: CLI, deck discovery, render orchestration, web builder. Depends on `manim-simplex`. |
| [`simplex-lectures-template`](https://github.com/shlomi-perles/simplex-lectures-template) | -- | GitHub Template. Pre-wired user lectures repo. |

The PyPI slot `simplex` was already taken by an unrelated project, and PyPI's
name-similarity guard rejects short variants, so this distribution publishes
as `simplex-web`. The *import* name is still
`simplex` -- both wheels ship `src/simplex/` **without** `__init__.py` and
Python's PEP 420 implicit namespace packages merge them at import time, so
`from simplex.engine import Remove` and `from simplex.cli.commands import app`
resolve regardless of which wheel ships the module.

## Quick start

```bash
# Install from PyPI:
pip install simplex-web

# Bootstrap a fresh checkout (Linux / macOS):
./scripts/bootstrap.sh

# Or on Windows:
.\\scripts\\bootstrap.ps1

# Scaffold a new deck and render it:
uv run simplex new my-first-deck
uv run simplex render my-first-deck

# Generate the portal and preview it locally:
uv run simplex build
uv run simplex serve
```

## Repository layout

```
simplex/
|-- src/simplex/          (no __init__.py -- PEP 420 namespace)
|   |-- deck/             DeckConfig, discovery, scaffolder
|   |-- render/           runner, reconcile, html/pdf/pptx, thumbnail
|   |-- web/              markdown notes + Jinja portal + SSE reload
|   `-- cli/              Typer entry point
|-- decks/                author content (one directory per deck)
`-- tests/

# Plugin half (mobjects, theme, slide bases) lives in manim-simplex.
```

Every directory ships a short `README.md` (<=50 lines) covering *scope*, *public surface*, and *don'ts*. Only this root README is long-form.

## Authoring a deck

A deck is three files plus optional assets:

```
decks/my-deck/
|-- deck.toml      slug, title, summary, tags, theme, scenes, quality
|-- slides.py      vanilla Manim, subclassing simplex.slides.*
|-- notes.md       English notes rendered into the portal
`-- assets/
```

Inside `slides.py` you write plain Manim -- the framework's only contribution is the base class plus a pure `make_chrome` factory:

```python
from manim import MathTex, ORIGIN, Write
from simplex.slides import BaseSlide, make_chrome
from simplex.theme.context import get_active_theme


class FermatLittleTheorem(BaseSlide):
    def setup(self) -> None:
        super().setup()
        chrome = make_chrome(get_active_theme(), self.region, header="Fermat's little theorem")
        self.add_to_canvas(**chrome.mobjects)
        self.region = chrome.body_region

    def construct(self) -> None:
        eq = MathTex(r"a^{p-1} \equiv 1 \pmod p")
        self.region.place(eq, ORIGIN)
        self.play(Write(eq))
        self.next_slide()  # bare first call -> MAIN named "Fermat Little Theorem"
```

No factories, no wrappers, no anti-corruption wall. The theme provides defaults, `self.region` provides bounded layout, and `clear_scene(exclude=...)` provides bulk fade-outs. Slide numbering / wall clock live in the RevealJS host (toggle via `[web]` in `deck.toml`), not the rendered frames.

## Theme tokens

Presets are frozen `Theme` instances, not subclasses, so swapping the visual identity at runtime is one assignment:

```python
from simplex.theme import active_theme, presets

with active_theme(presets.ACADEMIC_LIGHT):
    # all slides constructed here pick up the light palette
    ...
```

LaTeX preamble lives on `theme.latex.preamble`. Fixed-width prose blocks use the `TexPage` mobject (default 20 cm, override via `width_cm=…` kwarg or a class attribute on a subclass).

## Style + tooling

- Python **3.13+**, env + lockfile via **uv**, lint + format via **ruff**, types via **basedpyright --strict**.
- Configuration through frozen **Pydantic v2** models. No bare `dict[str, Any]`.
- See `STYLE.md` for the full rule set.

## License

MIT.
