"""Scene modules live alongside this file (e.g. `intro.py`).

Reference them from `deck.toml` as `entrypoints = ["slides.intro:Intro", ...]`;
the runner loads each entrypoint module directly. Don't re-export scene
classes here -- manim's discovery filters by `__module__`, so re-exports
are silently dropped.
"""
