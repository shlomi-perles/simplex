# Examples

Runnable demo scenes that double as integration smoke tests.

Each scene is intentionally small (single concept, ~30 LOC) and uses the
`manim-simplex` public API as a downstream user would.

## Running

From the repo root with the dev environment synced:

```bash
uv run manim -pql examples/hello_slide.py HelloSlide
uv run manim -pql examples/theme_demo.py ThemeDemo
uv run manim -pql examples/glyph_map_demo.py GlyphMapDemo
```

The `-pql` flag previews at low quality. Use `-pqh` for 1080p, `-qk` for
4K render-only.

## With manim-slides

To render as a slide deck (uses the `Slide` base class):

```bash
uv run manim-slides render examples/hello_slide.py HelloSlide
uv run manim-slides present HelloSlide
```

The plugin auto-activates via the `manim.plugins` entry-point as long as
the deck's `manim.cfg` declares `plugins = simplex`. For these examples
we keep a tiny `manim.cfg` next to them so they render with the Simplex
theme out of the box.
