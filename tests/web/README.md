# tests/web/

Tests for `simplex.web.notes` and `simplex.web.builder` -- no real `manim-slides`
invocation. The builder is exercised end-to-end with `render=False` so it emits
HTML without shelling out to Manim.

## Public surface

- `test_notes.py` -- dollar-math wraps content in `class="math inline"` /
  `class="math block"`; fenced code blocks survive.
- `test_builder.py` -- `build(render=False)` writes `index.html` and one page per deck.

## Don't

- Don't load KaTeX / Tailwind from a CDN inside tests. The HTML assertion is on
  the LaTeX markers that KaTeX picks up at page load.
- Don't depend on the order of decks in the index page -- assertions check for
  presence, not position.
