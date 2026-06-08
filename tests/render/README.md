# tests/render/

Tests for the timeline render pipeline: direct Manim runner subprocess
assembly, cue rebasing and theme validation, cue poster/thumbnail extraction,
and export helpers.

Tests that need real binaries skip or use PyAV fallbacks where possible so the
suite can still run offline.
