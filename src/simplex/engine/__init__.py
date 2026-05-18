"""Engine helpers that augment vanilla Manim."""

from simplex.engine.animations import (
    Remove,
    clear_scene,
    exit_for,
    register_exit,
    set_exit_animation,
)
from simplex.engine.defaults import apply_theme_defaults
from simplex.engine.region import Region
from simplex.engine.section_types import SimplexSectionType

__all__ = [
    "Region",
    "Remove",
    "SimplexSectionType",
    "apply_theme_defaults",
    "clear_scene",
    "exit_for",
    "register_exit",
    "set_exit_animation",
]
