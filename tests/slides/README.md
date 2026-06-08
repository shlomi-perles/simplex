# tests/slides/

Tests for `simplex.slides`: Simplex-owned cue recording, the transitional
`next_slide` alias, and the `make_chrome` purity contract.

## Conventions

- `test_base.py` uses a fake scene object so cue timing can be tested without
  a fully-initialised Manim renderer, camera, or file writer.
- `test_chrome.py` runs against `manim.config.frame_width` via
  `Region.full_frame()`; gated on `pytest.importorskip("manim")`.

## Don't

- Don't render a deck here. Cue unit tests should stay fast and isolated.
- Don't reach into Manim internals when a public Simplex cue API covers the
  behavior.
