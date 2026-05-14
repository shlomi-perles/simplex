"""Showcase deck -- scene modules live alongside this file.

Scene classes are kept in their defining modules (`scenes.py` here); the
runner loads each entrypoint module directly. We intentionally do NOT
re-export scene classes -- manim's `scene_classes_from_file` filters by
`__module__.startswith(loaded_module)`, so re-exported classes are dropped.
"""
