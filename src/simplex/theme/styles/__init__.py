"""Built-in Pygments code styles for Simplex.

Each style lives in its own module. The ``BUILTIN_STYLES`` mapping exposes
them by registration name so the theme system can look up and register any
style without importing all of them eagerly.
"""

from simplex.theme.styles.simplex_pycharm import SimplexPycharm
from simplex.theme.styles.simplex_solarized_light import SimplexSolarizedLight

BUILTIN_STYLES: dict[str, type] = {
    "simplex_pycharm": SimplexPycharm,
    "simplex_solarized_light": SimplexSolarizedLight,
}

__all__ = [
    "BUILTIN_STYLES",
    "SimplexPycharm",
    "SimplexSolarizedLight",
]
