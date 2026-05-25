"""Theme tokens and active-theme registry."""

from simplex.theme import presets
from simplex.theme.context import active_theme, get_active_theme
from simplex.theme.presets import SIMPLEX_DARK
from simplex.theme.pygments_style import (
    SimplexPycharm,
    SimplexSolarizedLight,
    register_all_builtin_styles,
    register_style,
)
from simplex.theme.tokens import (
    LatexProfile,
    Motion,
    Palette,
    Spacing,
    Theme,
    Typography,
    WebPalette,
)
from simplex.theme.web_css import render_web_css

__all__ = [
    "SIMPLEX_DARK",
    "LatexProfile",
    "Motion",
    "Palette",
    "SimplexPycharm",
    "SimplexSolarizedLight",
    "Spacing",
    "Theme",
    "Typography",
    "WebPalette",
    "active_theme",
    "get_active_theme",
    "presets",
    "register_all_builtin_styles",
    "register_style",
    "render_web_css",
]
