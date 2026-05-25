"""Engine helpers that augment vanilla Manim.

The engine ships animation primitives, layout helpers, and small custom
mobjects -- everything that *isn't* a Slide and *isn't* a theme token.

Cross-package types like ``SimplexSectionType`` live at the package root
(``simplex.section``) so the web builder and CLI can import them without
touching Manim.
"""

from simplex.engine.animations import (
    Remove,
    clear_scene,
    exit_for,
    register_exit,
    set_exit_animation,
)
from simplex.engine.code import HighlightResult
from simplex.engine.defaults import apply_theme_defaults
from simplex.engine.region import Region

__all__ = [
    "HighlightResult",
    "Region",
    "Remove",
    "apply_theme_defaults",
    "clear_scene",
    "exit_for",
    "register_exit",
    "set_exit_animation",
]
