"""Theme tokens and active-theme registry."""

from simplex.theme import presets
from simplex.theme.context import active_theme, get_active_theme, set_default_theme
from simplex.theme.palettes import (
    MANIM_DEFAULT,
    available_palette_names,
    code_styles_dir,
    palette_styles_dir,
    resolve_palette,
    theme_styles_dir,
)
from simplex.theme.palettes import (
    SIMPLEX_LIGHT as SIMPLEX_LIGHT_PALETTE,
)
from simplex.theme.presets import (
    SIMPLEX_DARK,
    SIMPLEX_LIGHT,
)
from simplex.theme.presets import (
    available_names as available_theme_names,
)
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
    "MANIM_DEFAULT",
    "SIMPLEX_DARK",
    "SIMPLEX_LIGHT",
    "SIMPLEX_LIGHT_PALETTE",
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
    "available_palette_names",
    "available_theme_names",
    "code_styles_dir",
    "get_active_theme",
    "palette_styles_dir",
    "presets",
    "register_all_builtin_styles",
    "register_style",
    "render_web_css",
    "resolve_palette",
    "set_default_theme",
    "theme_styles_dir",
]
