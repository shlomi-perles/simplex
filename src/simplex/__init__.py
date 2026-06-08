"""Convenience imports for the Simplex authoring API.

Keep this module light: exported objects are loaded lazily so CLI and web
modules can import ``simplex.web`` without eagerly importing Manim objects.
"""

# ruff: noqa: F401
# pyright: reportUnsupportedDunderAll=false, reportUnusedImport=false

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Any

_EXPORTS: dict[str, str] = {
    "Array": "simplex.mobjects",
    "ArrayCell": "simplex.mobjects",
    "ArrayEntry": "simplex.mobjects",
    "ArrayMob": "simplex.mobjects",
    "ArrayPointer": "simplex.mobjects",
    "ColorBar": "simplex.mobjects",
    "BaseSlide": "simplex.slides",
    "Caption": "simplex.engine.text",
    "Chrome": "simplex.slides",
    "DN": "simplex.engine.dynamics",
    "DeckManifest": "simplex.manifest",
    "DeckConfig": "simplex.deck",
    "DismissPaper": "simplex.mobjects",
    "Edge": "simplex.mobjects",
    "ExitAnim": "simplex.engine",
    "GhostSlideFade": "simplex.engine.ghost_fade",
    "HighlightResult": "simplex.engine",
    "MainSlide": "simplex.manifest",
    "Node": "simplex.mobjects",
    "OutlinePart": "simplex.slides",
    "OutlineProgressBar": "simplex.mobjects",
    "OutlineScene": "simplex.slides",
    "Paper": "simplex.mobjects",
    "PickPage": "simplex.mobjects",
    "Region": "simplex.engine",
    "SIMPLEX_DARK": "simplex.theme.presets",
    "SIMPLEX_LIGHT": "simplex.theme.presets",
    "OpenGLSphere": "simplex.mobjects",
    "ScalarFieldSurface": "simplex.mobjects",
    "ShowPaper": "simplex.mobjects",
    "Sphere": "simplex.mobjects",
    "Slide": "simplex.slides",
    "SimplexSectionType": "simplex.section",
    "Subsection": "simplex.manifest",
    "TexPage": "simplex.engine.text",
    "ThreeDSlide": "simplex.slides",
    "TransformByGlyphMap": "simplex.engine.glyph_map",
    "VT": "simplex.engine.dynamics",
    "active_theme": "simplex.theme",
    "available_palette_names": "simplex.theme",
    "available_theme_names": "simplex.theme",
    "apply_theme_defaults": "simplex.engine",
    "colorize_surface": "simplex.mobjects",
    "bounding_box": "simplex.engine.debug",
    "clear_scene": "simplex.engine",
    "code_block": "simplex.engine.code",
    "code_explain": "simplex.engine.code",
    "code_with_math": "simplex.engine.code",
    "color_substrings": "simplex.engine.text",
    "debug_glyph": "simplex.engine.debug",
    "debug_glyphs": "simplex.engine.debug",
    "discover": "simplex.deck",
    "exit_for": "simplex.engine",
    "get_active_theme": "simplex.theme",
    "get_frame_center": "simplex.engine.geometry",
    "get_surrounding_rectangle": "simplex.engine.geometry",
    "highlight_code_lines": "simplex.engine.code",
    "indexx_labels": "simplex.engine.debug",
    "keep_orientation": "simplex.engine.dynamics",
    "maintain_apparent_stroke_width": "simplex.engine.dynamics",
    "make_chrome": "simplex.slides",
    "minipage_cm_for_page_width": "simplex.engine.text",
    "munits_per_cm": "simplex.engine.text",
    "presets": "simplex.theme",
    "pseudocode_block": "simplex.engine.code",
    "register_exit": "simplex.engine",
    "resolve_palette": "simplex.theme",
    "scale_to_fit": "simplex.engine.scaling",
    "scale_to_fit_mobject": "simplex.engine.scaling",
    "scaffold": "simplex.deck",
    "search_shape_in_text": "simplex.engine.text",
    "set_exit_animation": "simplex.engine",
    "theme_styles_dir": "simplex.theme",
}

__all__ = sorted(_EXPORTS)


def __getattr__(name: str) -> Any:
    if name not in _EXPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module = import_module(_EXPORTS[name])
    value = getattr(module, name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))


if TYPE_CHECKING:
    from simplex.deck import DeckConfig, discover, scaffold
    from simplex.engine import (
        ExitAnim,
        HighlightResult,
        Region,
        apply_theme_defaults,
        clear_scene,
        exit_for,
        register_exit,
        set_exit_animation,
    )
    from simplex.engine.code import (
        code_block,
        code_explain,
        code_with_math,
        highlight_code_lines,
        pseudocode_block,
    )
    from simplex.engine.debug import bounding_box, debug_glyph, debug_glyphs, indexx_labels
    from simplex.engine.dynamics import DN, VT, keep_orientation, maintain_apparent_stroke_width
    from simplex.engine.geometry import get_frame_center, get_surrounding_rectangle
    from simplex.engine.ghost_fade import GhostSlideFade
    from simplex.engine.glyph_map import TransformByGlyphMap
    from simplex.engine.scaling import scale_to_fit, scale_to_fit_mobject
    from simplex.engine.text import (
        Caption,
        TexPage,
        color_substrings,
        minipage_cm_for_page_width,
        munits_per_cm,
        search_shape_in_text,
    )
    from simplex.manifest import DeckManifest, MainSlide, Subsection
    from simplex.mobjects import (
        Array,
        ArrayCell,
        ArrayEntry,
        ArrayMob,
        ArrayPointer,
        ColorBar,
        DismissPaper,
        Edge,
        Node,
        OpenGLSphere,
        OutlineProgressBar,
        Paper,
        PickPage,
        ScalarFieldSurface,
        ShowPaper,
        Sphere,
        colorize_surface,
    )
    from simplex.section import SimplexSectionType
    from simplex.slides import (
        BaseSlide,
        Chrome,
        OutlinePart,
        OutlineScene,
        Slide,
        ThreeDSlide,
        make_chrome,
    )
    from simplex.theme import (
        active_theme,
        available_palette_names,
        available_theme_names,
        get_active_theme,
        presets,
        resolve_palette,
        theme_styles_dir,
    )
    from simplex.theme.presets import SIMPLEX_DARK, SIMPLEX_LIGHT
