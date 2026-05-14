"""Engine helpers that augment vanilla Manim."""

from simplex.engine.animations import Remove, set_exit_animation
from simplex.engine.config import configure_manim
from simplex.engine.defaults import apply_theme_defaults
from simplex.engine.region import Region

__all__ = [
    "Region",
    "Remove",
    "apply_theme_defaults",
    "configure_manim",
    "set_exit_animation",
]
