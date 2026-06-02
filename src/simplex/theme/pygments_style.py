"""Pygments style registry shared by the engine (videos) and the web
(notes code blocks). Kept manim-free so the web build doesn't pull manim in.

Individual styles live under ``simplex.theme.styles``. This module provides
the registration helper and re-exports the built-in styles for convenience.
"""

import importlib.util
import sys
import types
from pathlib import Path

from pygments.style import Style
from pygments.styles import get_style_by_name
from pygments.util import ClassNotFound

from simplex.theme.styles import BUILTIN_STYLES, SimplexPycharm, SimplexSolarizedLight

__all__ = [
    "BUILTIN_STYLES",
    "SimplexPycharm",
    "SimplexSolarizedLight",
    "background_color_for_style",
    "load_custom_styles",
    "register_style",
    "resolve_style",
    "style_name_for_class",
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


def style_name_for_class(style_cls: type[Style]) -> str:
    """Return the registered Simplex/Pygments style name for ``style_cls``."""
    return _class_name_to_style_name(style_cls.__name__)


def background_color_for_style(style_cls: type[Style]) -> str:
    """Return a code style's background, falling back to Simplex dark."""
    background = style_cls.__dict__.get("background_color")
    if isinstance(background, str) and background:
        return background
    return SimplexPycharm.background_color


def register_all_builtin_styles() -> None:
    """Register every built-in Simplex style with Pygments."""
    for name, cls in BUILTIN_STYLES.items():
        register_style(cls, name)


def load_custom_styles(directory: Path) -> dict[str, type[Style]]:
    """Import project-local Pygments ``Style`` subclasses from ``directory``."""
    out: dict[str, type[Style]] = {}
    if not directory.is_dir():
        return out

    for path in sorted(directory.glob("*.py")):
        if path.name.startswith("_"):
            continue
        module_name = f"_simplex_custom_style_{path.stem}"
        module = None
        try:
            spec = importlib.util.spec_from_file_location(module_name, path)
            if spec is None or spec.loader is None:
                continue
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
        except Exception:
            module = None
        if module is None:
            continue
        for obj in vars(module).values():
            if (
                isinstance(obj, type)
                and issubclass(obj, Style)
                and obj is not Style
                and obj.__module__ == module_name
            ):
                out[_class_name_to_style_name(obj.__name__)] = obj
                out[obj.__name__] = obj
                out.setdefault(path.stem, obj)
    return out


def resolve_style(name: str | None, *, default: type[Style]) -> type[Style]:
    """Resolve a configured Pygments style name.

    Built-in Simplex styles accept either their registry name
    (``simplex_solarized_light``) or class name (``SimplexSolarizedLight``).
    Project-local custom styles in ``simplex_themes/code_styles`` and any
    Pygments-installed style name are accepted too.
    """
    if name is None or not name.strip():
        return default

    register_all_builtin_styles()
    from simplex.theme.palettes import code_styles_dir

    custom_styles = load_custom_styles(code_styles_dir())
    raw = name.strip()
    candidates = [raw]
    class_like = _class_name_to_style_name(raw)
    if class_like != raw:
        candidates.append(class_like)

    for candidate in candidates:
        if candidate in BUILTIN_STYLES:
            return BUILTIN_STYLES[candidate]
        if candidate in custom_styles:
            return custom_styles[candidate]
        try:
            return get_style_by_name(candidate)
        except ClassNotFound:
            continue

    builtins = ", ".join(sorted(BUILTIN_STYLES))
    raise ValueError(
        f"unknown Pygments style {name!r}; use a Pygments style name, a custom "
        f"style in simplex_themes/code_styles, or one of: {builtins}"
    )


def _class_name_to_style_name(name: str) -> str:
    """``SimplexPycharm`` -> ``simplex_pycharm``."""
    result: list[str] = []
    for i, ch in enumerate(name):
        if ch.isupper() and i > 0:
            result.append("_")
        result.append(ch.lower())
    return "".join(result)
