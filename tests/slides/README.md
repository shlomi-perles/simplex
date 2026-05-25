# tests/slides/

Tests for `simplex.slides`: `BaseSlide.next_slide` section-type
resolution (silent auto-promotion on first bare call, SUB after a named
main, explicit overrides) and the `make_chrome` purity contract.

## Conventions

- `test_base.py` uses a `_StubSlide` that re-implements the resolution +
  forward path without calling `super().next_slide`, so it doesn't need
  a fully-initialised `Scene` (no renderer, no camera, no file output).
- `test_chrome.py` runs against `manim.config.frame_width` via
  `Region.full_frame()`; gated on `pytest.importorskip("manim")`.

## Don't

- Don't render a deck here. The manim-slides subprocess is too slow for
  a unit test loop.
- Don't reach into manim-slides' canvas internals; the public
  `add_to_canvas` API is the boundary.
