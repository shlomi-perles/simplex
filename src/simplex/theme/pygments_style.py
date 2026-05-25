"""Pygments style registry shared by the engine (videos) and the web
(notes code blocks). Kept manim-free so the web build doesn't pull manim in.

Individual styles live under ``simplex.theme.styles``. This module provides
the registration helper and re-exports the built-in styles for convenience.
"""

import sys
import types

from pygments.style import Style

from simplex.theme.styles import BUILTIN_STYLES, SimplexPycharm, SimplexSolarizedLight

__all__ = [
    "BUILTIN_STYLES",
    "SimplexPycharm",
    "SimplexSolarizedLight",
    "register_style",
]


def register_style(style_cls: type[Style], style_name: str | None = None) -> None:
    """Register a Pygments ``Style`` subclass under ``style_name``. Idempotent.

    When *style_name* is omitted the class name is lowercased with
    underscores (``SimplexPycharm`` -> ``simplex_pycharm``).
    """
    import pygments.styles

    if style_name is None:
        style_name = _class_name_to_style_name(style_cls.__name__)
    if style_name in pygments.styles.STYLE_MAP:
        return
    cls_name = style_cls.__name__
    mod_name = f"pygments.styles.{style_name}"
    module = types.ModuleType(mod_name)
    setattr(module, cls_name, style_cls)
    setattr(pygments.styles, style_name, module)
    sys.modules[mod_name] = module
    style_map: dict[str, str] = pygments.styles.STYLE_MAP  # type: ignore[assignment]
    style_map[style_name] = f"{style_name}::{cls_name}"
    # Pygments builds _STYLE_NAME_TO_MODULE_MAP and STYLES at import time;
    # update both so ``get_style_by_name`` resolves without fallback heuristics.
    styles: dict[str, tuple[str, str, tuple[str, ...]]] = pygments.styles.STYLES  # type: ignore[assignment]
    styles[cls_name] = (mod_name, style_name, ())
    name_map: dict[str, tuple[str, str]] = pygments.styles._STYLE_NAME_TO_MODULE_MAP  # type: ignore[assignment]
    name_map[style_name] = (mod_name, cls_name)


def register_all_builtin_styles() -> None:
    """Register every built-in Simplex style with Pygments."""
    for name, cls in BUILTIN_STYLES.items():
        register_style(cls, name)


def _class_name_to_style_name(name: str) -> str:
    """``SimplexPycharm`` -> ``simplex_pycharm``."""
    result: list[str] = []
    for i, ch in enumerate(name):
        if ch.isupper() and i > 0:
            result.append("_")
        result.append(ch.lower())
    return "".join(result)
