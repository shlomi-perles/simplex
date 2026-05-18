# tests/render/

Tests for the render pipeline: runner subprocess assembly, native-section
reconcile, our RevealJS HTML emitter, ffmpeg thumbnail extraction.

Tests that need real binaries (ffmpeg / ffprobe / manim-slides) skip when
those are missing on PATH so the suite runs offline.
