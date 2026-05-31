# ManimCE OpenGL Compatibility Plan

## Summary

Simplex supports ManimCE's OpenGL renderer, not the legacy `manimlib` / 3b1b
stack. OpenGL is selected before scene import for Simplex renders, while
Manim-style file-level `config.renderer = "opengl"` remains valid for
standalone scene files.

## Key Decisions

- Canonical authoring imports are `simplex.Slide` and `simplex.ThreeDSlide`.
  `BaseSlide` remains a compatibility alias for `Slide`.
- Deck metadata is the preferred renderer source. The canonical form is one
  ordered list:
  `entrypoints = ["slides.intro:Intro", "slides.surface:Surface@opengl"]`.
- Plain string entrypoints render with Cairo unless the source file declares a
  file-level renderer; `@opengl` pins only that one entrypoint to OpenGL.
- File-level `config.renderer = "opengl"` is detected as a fallback when
  entrypoint metadata does not declare a renderer.
- If deck metadata and file-level renderer config conflict, rendering fails
  with a clear error.
- Simplex's runner passes `--renderer=opengl --write_to_movie` for OpenGL
  groups. `manim-slides.Slide` already forces movie output, but the CLI flag
  matches ManimCE's OpenGL behavior explicitly.

## Implementation Surface

- `simplex.deck.config` normalizes compact string entrypoints into
  `SceneEntrypoint` objects and resolves render batches by source file and
  renderer.
- `simplex.render.runner` renders Cairo and OpenGL batches separately.
- `simplex.engine.opengl_compat` centralizes Cairo/OpenGL mobject checks and
  bounding-box point lookup.
- Simplex mobjects that subclass Manim mobject bases opt into Manim's
  `ConvertToOpenGL` metaclass.
- Showcase OpenGL scenes use `ThreeDSlide` instead of multiple inheritance.

## Verification

- Unit tests cover compact renderer-marked entrypoints, renderer fallback detection,
  metadata conflicts, OpenGL runner flags, public slide imports, and Region /
  critical-point behavior with OpenGL mobjects.
- The showcase deck is copied into `simplex-test-cases` after implementation
  and smoke-rendered there with the editable Simplex package.
