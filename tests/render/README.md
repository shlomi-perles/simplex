# tests/render/

Tests for the render pipeline: manim-slides JSON manifest parsing,
thumbnail caching, runner subprocess assembly, our RevealJS HTML emitter.

Tests that need real binaries (ffmpeg / ffprobe / manim-slides) skip when
those are missing on PATH so the suite runs offline.
