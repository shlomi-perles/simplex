# Migration to v0.2.0 — the three-repo split

This document covers **Phase 3** of `PLAN_v2.md`: splitting the current
single `simplex` package into three repositories. Phases 0-2 are already
done on the `claude/setup-manim-installation-4p24R` branch and pushed.

I (Claude in this session) cannot create the two sibling repos -- my MCP
scope only covers `shlomi-perles/simplex`. The steps below are
copy-paste-ready for you to execute locally.

## Why three repos

| Repo | PyPI | Role |
|---|---|---|
| `shlomi-perles/simplex-core` | `manim-simplex` | The manim plugin: mobjects, theme, `BaseSlide`, plugin entry-point. **No CLI, no web builder.** |
| `shlomi-perles/simplex` (this repo) | `simplex` | The platform: CLI, deck discovery, render orchestration, web builder. Depends on `manim-simplex`. |
| `shlomi-perles/simplex-lectures-template` | -- | GitHub Template. Pre-wired user lectures repo. |

The trick: both PyPI distributions ship a `src/simplex/` directory **without**
`__init__.py`. Python's PEP 420 implicit namespace packages merge them at
import time, so `from simplex.engine import …` resolves regardless of
which wheel ships the module.

## Step 1 — Create the two new GitHub repos

In the GitHub UI:

```
shlomi-perles/simplex-core              # private or public, no template
shlomi-perles/simplex-lectures-template # public, "Template repository" toggled ON
```

Or via `gh`:

```bash
gh repo create shlomi-perles/simplex-core --public --description "Simplex manim plugin"
gh repo create shlomi-perles/simplex-lectures-template --public --description "Template for Simplex lecture sites"
# Then: settings -> "Template repository" -> ON
```

## Step 2 — Populate `simplex-core`

Modules that move out of `simplex` and into `simplex-core/src/simplex/`:

```
src/simplex/plugin.py
src/simplex/section_types.py     <-- currently under engine/
src/simplex/engine/animations.py
src/simplex/engine/code.py
src/simplex/engine/debug.py
src/simplex/engine/defaults.py
src/simplex/engine/dynamics.py
src/simplex/engine/geometry.py
src/simplex/engine/region.py
src/simplex/engine/scaling.py
src/simplex/engine/text.py
src/simplex/engine/transforms.py
src/simplex/engine/__init__.py
src/simplex/theme/                (all of it, including web_css.py)
src/simplex/slides/               (all of it: base, chrome, components, README)
```

Note: in `simplex-core` the file `src/simplex/engine/section_types.py`
should stay where it currently lives (under `engine/`) for backward
compatibility with `from simplex.engine import SimplexSectionType`. The
table above just lists files; the directory layout is preserved.

`simplex-core/pyproject.toml`:

```toml
[project]
name = "manim-simplex"
version = "0.2.0"
description = "Manim plugin: theme tokens, mobjects, slide hierarchy."
readme = "README.md"
requires-python = ">=3.14"
license = { text = "MIT" }
authors = [{ name = "Shlomi Perles" }]
dependencies = [
    "manim>=0.20.1",
    "manim-slides>=5.1.7",
    "pydantic>=2.7",
    "pygments>=2.18",
]

[project.entry-points."manim.plugins"]
simplex = "simplex.plugin:activate"

[dependency-groups]
dev = [
    "pytest>=8",
    "syrupy>=4.6",
    "ruff>=0.6",
    "basedpyright>=1.13",
    "pre-commit>=3.7",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/simplex"]

[tool.basedpyright]
include = ["src", "tests"]
pythonVersion = "3.14"
typeCheckingMode = "strict"
reportMissingTypeStubs = false
reportUnknownMemberType = false
reportUnknownVariableType = false
reportUnknownArgumentType = false
```

**Critical:** do NOT create `simplex-core/src/simplex/__init__.py`. The
namespace must be implicit (PEP 420) so the `simplex` distribution can
contribute the `cli/`, `deck/`, `render/`, `web/` siblings.

CI for `simplex-core` (`.github/workflows/ci.yml`):

```yaml
name: CI
on: { push: { branches: [main] }, pull_request: }
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: |
          sudo apt-get update
          sudo apt-get install -y texlive-latex-extra texlive-fonts-recommended \
                                  ffmpeg libcairo2-dev libpango1.0-dev
      - uses: astral-sh/setup-uv@v3
      - run: uv sync
      - run: uv run ruff check .
      - run: uv run ruff format --check .
      - run: uv run basedpyright
      - run: uv run pytest -q
      - name: Plugin activate smoke
        run: uv run python -c "import simplex.plugin; simplex.plugin.activate(); print('ok')"
```

PyPI publish workflow (`.github/workflows/publish-pypi.yml`):

```yaml
name: Publish to PyPI
on:
  push:
    tags: ["v*"]
jobs:
  publish:
    runs-on: ubuntu-latest
    environment: pypi
    permissions: { id-token: write }
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
      - run: uv build
      - uses: pypa/gh-action-pypi-publish@release/v1
```

## Step 3 — Strip moved modules from `simplex` (this repo)

After Step 2 lands `simplex-core` v0.2.0 on PyPI (or a TestPyPI release),
in **this repo** (`simplex`):

```bash
git rm -r src/simplex/plugin.py \
          src/simplex/engine/ \
          src/simplex/theme/ \
          src/simplex/slides/

# pyproject.toml: add manim-simplex dep, remove the entry-point block.
```

Updated `pyproject.toml` dependency list:

```toml
dependencies = [
    "manim-simplex>=0.2.0",   # <-- the new dep
    "manim-slides>=5.1.7",
    "pydantic>=2.7",
    "pydantic-settings>=2.3",
    "typer>=0.12",
    "rich>=13.7",
    "structlog>=24.1",
    "jinja2>=3.1",
    "markdown-it-py>=3.0",
    "mdit-py-plugins>=0.4",
    "pygments>=2.18",
    "platformdirs>=4.2",
    "tomli-w>=1.0",
    "watchfiles>=0.24",
]
```

Remove the `[project.entry-points."manim.plugins"]` block from
`pyproject.toml` (the entry-point now lives in `manim-simplex`).

Verify namespace works locally:

```bash
uv sync
uv run python -c "from simplex.engine import Remove; from simplex.cli.commands import app; print('ok')"
```

If hatchling complains about an empty package or auto-injects an
`__init__.py`, switch the build backend to setuptools:

```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[tool.setuptools.packages.find]
where = ["src"]
include = ["simplex*"]
namespaces = true
```

## Step 4 — Populate `simplex-lectures-template`

Copy from `decks/_template/` into the new repo's `decks/_example/`:

```
decks/_template/deck.toml      -> decks/_example/deck.toml
decks/_template/notes.md       -> decks/_example/notes.md
decks/_template/refs.bib       -> decks/_example/refs.bib
decks/_template/manim.cfg      -> decks/_example/manim.cfg
decks/_template/slides/        -> decks/_example/slides/
decks/_template/assets/        -> decks/_example/assets/
```

Root files for the template repo:

`pyproject.toml`:

```toml
[project]
name = "my-lectures"
version = "0.0.0"
description = "Lectures site built with Simplex."
requires-python = ">=3.14"
dependencies = ["simplex-py>=0.2.0"]
```

`.python-version`:

```
3.14
```

`ruff.toml`:

```toml
target-version = "py314"
line-length = 100

[lint]
select = ["E", "W", "F", "I", "N", "B", "UP", "SIM", "TID", "PTH", "RUF"]
ignore = ["E501"]

[lint.per-file-ignores]
"decks/**/slides.py" = ["E402", "F401", "F403", "F405", "N801", "N802", "N803", "N806", "I001", "PLR2004", "T201", "S101"]
"decks/**/slides/**/*.py" = ["E402", "F401", "F403", "F405", "N801", "N802", "N803", "N806", "I001", "PLR2004", "T201", "S101"]
```

`.gitignore`:

```
.venv/
__pycache__/
.ruff_cache/
.pytest_cache/
media/
site/
*.egg-info/
.python-version
```

`site.toml`:

```toml
brand = "My Lectures"
tagline = "Replace this with your tagline."
base_url = "/"
```

`.github/workflows/deploy.yml` (this is the single CI file the user
needs; uses `actions/deploy-pages@v4` with no `gh-pages` branch):

```yaml
name: Deploy
on:
  push: { branches: [main] }
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: pages
  cancel-in-progress: true

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: |
          sudo apt-get update
          sudo apt-get install -y texlive-latex-extra texlive-fonts-recommended \
                                  ffmpeg libcairo2-dev libpango1.0-dev
      - uses: astral-sh/setup-uv@v3
      - run: uv sync
      - uses: actions/cache@v4
        with:
          path: |
            site/decks/*/media
            ~/.cache/uv
          key: simplex-${{ hashFiles('uv.lock', 'decks/**/deck.toml', 'decks/**/slides/**/*.py', 'decks/**/manim.cfg') }}
          restore-keys: simplex-
      - run: uv run simplex build
      - uses: actions/upload-pages-artifact@v3
        with: { path: site }
  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - id: deployment
        uses: actions/deploy-pages@v4
```

`README.md`:

```markdown
# My Lectures

Built with [Simplex](https://github.com/shlomi-perles/simplex).

## Quick start

1. Click **Use this template** on GitHub to create your own repo.
2. Enable Pages: **Settings -> Pages -> Source: GitHub Actions**.
3. Locally: `uv sync && uv run simplex new my-first-deck`.
4. Push to `main` -- the `Deploy` workflow publishes to GitHub Pages.

Optional: `uv run simplex serve --watch` for live reload during editing.
```

After populating, mark the repo as a GitHub Template via settings.

## Step 5 — Cross-repo smoke test

After `manim-simplex` is on PyPI (or TestPyPI):

```bash
gh repo create my-lectures-test --template shlomi-perles/simplex-lectures-template --clone
cd my-lectures-test
uv sync
uv run simplex new test-deck
# edit decks/test-deck/slides/scenes.py ...
uv run simplex build
uv run simplex serve --watch          # open http://localhost:8000
git push
# wait ~20 min for first cold cache; check Pages URL appears in Actions run
```

## Step 6 — Tag releases

In order:

```bash
# simplex-core
git tag v0.2.0 && git push --tags    # publishes manim-simplex to PyPI

# simplex (this repo)
git tag v0.2.0 && git push --tags    # publishes simplex to PyPI

# simplex-lectures-template
git tag v0.2.0 && git push --tags    # informational only; no PyPI
```

## Known caveats

- **PEP 420 namespace with hatchling**: confirm the wheel does not
  auto-inject `simplex/__init__.py`. If it does, switch to setuptools
  with `find_namespace_packages` (snippet in Step 3).
- **GitHub Pages source**: each lectures repo must flip
  Settings -> Pages -> Source from "Deploy from a branch" to
  "GitHub Actions" once. The template README should call this out.
- **`watchfiles` debounce**: 200ms default in our config; SSE doesn't
  spam the browser on bulk saves but can land twice in a row if a build
  is in flight. Acceptable; can tune later.
- **`section_type` round-trip**: confirm via `cat
  media/videos/<src>/<q>/sections/<Scene>.json` after the first real
  render that `type` reads `simplex.main` / `simplex.sub` etc. The
  `BaseSlideConfig.wrapper` should leave `section_type` untouched; this
  is just a one-shot verification.
