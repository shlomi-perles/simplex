"""Manim palette registry and iTerm2 color-scheme mapping.

Simplex themes are semantic: they talk about ``accent``, ``edge``, and
``vertex`` colors. This module resolves a concrete Manim color palette first,
then derives those semantic defaults from the resolved constants. Custom
palettes use the same export shape as Theme Studio.
"""

from __future__ import annotations

import json
import os
import plistlib
import re
from collections.abc import Mapping
from dataclasses import dataclass
from functools import lru_cache
from importlib import resources
from pathlib import Path
from typing import Any

MANIM_DEFAULT = "manim_default"
SIMPLEX_LIGHT = "simplex_light"
CUSTOM_THEME_DIR = "simplex_themes"
CODE_STYLES_DIR = "code_styles"
PALETTE_STYLES_DIR = "palette_styles"
THEME_STYLES_DIR = "themes"

DEFAULT_PALETTE_PREVIEW: tuple[str, ...] = (
    SIMPLEX_LIGHT,
    "Ayu Light",
    "Belafonte Day",
    "Catppuccin Latte",
    "Cursor Light",
    "Flexoki Light",
    "Gruvbox Light Hard",
    "London Columbia Road",
    "Monokai Pro Light Sun",
    "Rose Pine Dawn",
    MANIM_DEFAULT,
)

_MANIM_FAMILIES: dict[str, tuple[str, int]] = {
    "BLUE": ("blue", 4),
    "TEAL": ("teal", 6),
    "GREEN": ("green", 2),
    "YELLOW": ("yellow", 3),
    "GOLD": ("gold", 11),
    "RED": ("red", 1),
    "MAROON": ("maroon", 9),
    "PURPLE": ("purple", 5),
}
_SHADE_TRANSFORMS = {
    "A": ("lighter", 0.2),
    "B": ("lighter", 0.1),
    "C": ("none", 0.0),
    "D": ("darker", 0.1),
    "E": ("darker", 0.2),
}
_DEFAULT_MANIM_COLORS: dict[str, str] = {
    "BLUE_A": "#C7E9F1",
    "BLUE_B": "#9CDCEB",
    "BLUE_C": "#58C4DD",
    "BLUE_D": "#29ABCA",
    "BLUE_E": "#236B8E",
    "BLUE": "#58C4DD",
    "TEAL_A": "#ACEAD7",
    "TEAL_B": "#76DDC0",
    "TEAL_C": "#5CD0B3",
    "TEAL_D": "#55C1A7",
    "TEAL_E": "#49A88F",
    "TEAL": "#5CD0B3",
    "GREEN_A": "#C9E2AE",
    "GREEN_B": "#A6CF8C",
    "GREEN_C": "#83C167",
    "GREEN_D": "#77B05D",
    "GREEN_E": "#699C52",
    "GREEN": "#83C167",
    "YELLOW_A": "#FFF1B6",
    "YELLOW_B": "#FFEA94",
    "YELLOW_C": "#F7D96F",
    "YELLOW_D": "#F4D345",
    "YELLOW_E": "#E8C11C",
    "YELLOW": "#F7D96F",
    "GOLD_A": "#F7C797",
    "GOLD_B": "#F9B775",
    "GOLD_C": "#F0AC5F",
    "GOLD_D": "#E1A158",
    "GOLD_E": "#C78D46",
    "GOLD": "#F0AC5F",
    "RED_A": "#F7A1A3",
    "RED_B": "#FF8080",
    "RED_C": "#FC6255",
    "RED_D": "#E65A4C",
    "RED_E": "#CF5044",
    "RED": "#FC6255",
    "MAROON_A": "#ECABC1",
    "MAROON_B": "#EC92AB",
    "MAROON_C": "#C55F73",
    "MAROON_D": "#A24D61",
    "MAROON_E": "#94424F",
    "MAROON": "#C55F73",
    "PURPLE_A": "#CAA3E8",
    "PURPLE_B": "#B189C6",
    "PURPLE_C": "#9A72AC",
    "PURPLE_D": "#715582",
    "PURPLE_E": "#644172",
    "PURPLE": "#9A72AC",
    "GRAY_A": "#DDDDDD",
    "GRAY_B": "#BBBBBB",
    "GRAY_C": "#888888",
    "GRAY_D": "#444444",
    "GRAY_E": "#222222",
    "GREY_A": "#DDDDDD",
    "GREY_B": "#BBBBBB",
    "GREY_C": "#888888",
    "GREY_D": "#444444",
    "GREY_E": "#222222",
    "GRAY": "#888888",
    "GREY": "#888888",
    "WHITE": "#FFFFFF",
    "BLACK": "#000000",
    "PINK": "#D147BD",
    "LIGHT_PINK": "#DC75CD",
    "ORANGE": "#FF862F",
    "LIGHT_BROWN": "#CD853F",
    "DARK_BROWN": "#8B4513",
    "GRAY_BROWN": "#736357",
    "GREY_BROWN": "#736357",
    "DARK_BLUE": "#236B8E",
}


@dataclass(frozen=True)
class ManimPalette:
    """Fully resolved palette values for Manim and Simplex."""

    name: str
    background: str
    colors: Mapping[str, str]


def project_root() -> Path:
    """Return the repo root used for ``simplex_themes`` lookups."""
    configured = os.environ.get("SIMPLEX_PROJECT_ROOT")
    if configured:
        return Path(configured)
    return Path.cwd()


def code_styles_dir(repo_root: Path | None = None) -> Path:
    """Return the project-local custom Pygments style directory."""
    return (repo_root or project_root()) / CUSTOM_THEME_DIR / CODE_STYLES_DIR


def palette_styles_dir(repo_root: Path | None = None) -> Path:
    """Return the project-local custom palette directory."""
    return (repo_root or project_root()) / CUSTOM_THEME_DIR / PALETTE_STYLES_DIR


def theme_styles_dir(repo_root: Path | None = None) -> Path:
    """Return the project-local custom theme directory."""
    return (repo_root or project_root()) / CUSTOM_THEME_DIR / THEME_STYLES_DIR


def resolve_palette(name: str, *, repo_root: Path | None = None) -> ManimPalette:
    """Resolve a built-in, vendored iTerm2, or project-local custom palette."""
    name = name.strip()
    custom_ansi, custom_direct = load_custom_palettes(palette_styles_dir(repo_root))
    if name in custom_direct:
        return _palette_from_export(name, custom_direct[name])
    if name == SIMPLEX_LIGHT:
        return _palette_from_export(SIMPLEX_LIGHT, _load_simplex_light_export())
    if name == MANIM_DEFAULT:
        return ManimPalette(MANIM_DEFAULT, "#000000", dict(_DEFAULT_MANIM_COLORS))
    if name in custom_ansi:
        return _palette_from_iterm(name, custom_ansi[name])

    iterm = load_vendored_iterm_palettes()
    if name in iterm:
        return _palette_from_iterm(name, iterm[name])

    known = ", ".join(available_palette_names(repo_root=repo_root)[:12])
    raise KeyError(f"unknown Manim palette {name!r}; known examples: {known}")


def available_palette_names(*, repo_root: Path | None = None) -> tuple[str, ...]:
    """Return all known palette names, with custom palettes taking precedence."""
    custom_ansi, custom_direct = load_custom_palettes(palette_styles_dir(repo_root))
    names = set(load_vendored_iterm_palettes())
    names.update(custom_ansi)
    names.update(custom_direct)
    names.update({MANIM_DEFAULT, SIMPLEX_LIGHT})
    return tuple(sorted(names))


def semantic_palette_for(name: str, *, repo_root: Path | None = None) -> dict[str, str]:
    """Derive Simplex's semantic video palette from a Manim palette."""
    palette = resolve_palette(name, repo_root=repo_root)
    colors = palette.colors
    return {
        "background": palette.background,
        "font": colors.get("WHITE", "#FFFFFF"),
        "accent": colors.get("GOLD", colors.get("BLUE", "#58C4DD")),
        "vertex": colors.get("BLUE_E", colors.get("BLUE", "#236B8E")),
        "vertex_stroke": colors.get("BLUE", "#58C4DD"),
        "edge": colors.get("WHITE", "#FFFFFF"),
        "weight": colors.get("YELLOW", "#F7D96F"),
        "visited": colors.get("GREEN", "#83C167"),
        "label": colors.get("WHITE", "#FFFFFF"),
        "distance": colors.get("ORANGE", "#FF862F"),
    }


def web_palette_for(name: str, *, repo_root: Path | None = None) -> dict[str, str]:
    """Derive default web CSS variables from a Manim palette."""
    palette = resolve_palette(name, repo_root=repo_root)
    colors = palette.colors
    return {
        "accent": colors.get("GOLD", colors.get("BLUE", "#58C4DD")),
        "background": palette.background,
        "surface": colors.get("GRAY_A", palette.background),
        "text_primary": colors.get("WHITE", "#FFFFFF"),
        "text_muted": colors.get("GRAY_C", "#888888"),
        "link": colors.get("BLUE", "#58C4DD"),
    }


def studio_palette_data(*, repo_root: Path | None = None) -> dict[str, object]:
    """Return the JSON-serializable palette payload expected by Theme Studio."""
    custom_ansi, custom_direct_exports = load_custom_palettes(palette_styles_dir(repo_root))
    palette_colors = dict(load_vendored_iterm_palettes())
    palette_colors.update(custom_ansi)

    direct = {
        MANIM_DEFAULT: _colors_to_swatches(_DEFAULT_MANIM_COLORS, "#000000"),
        SIMPLEX_LIGHT: _json_palette_to_swatches(_load_simplex_light_export()),
    }
    direct.update(
        {name: _json_palette_to_swatches(data) for name, data in custom_direct_exports.items()}
    )

    custom_names = sorted(set(custom_ansi) | set(custom_direct_exports))
    all_names = sorted(set(palette_colors) | set(direct))
    preview = list(
        dict.fromkeys(
            custom_names
            + [name for name in DEFAULT_PALETTE_PREVIEW if name in palette_colors or name in direct]
        )
    )
    default_theme = SIMPLEX_LIGHT if SIMPLEX_LIGHT in preview else (preview[0] if preview else "")
    return {
        "PALETTE_COLORS": palette_colors,
        "PALETTE_DIRECT": direct,
        "PALETTE_LIST": all_names,
        "PALETTE_PREVIEW": preview,
        "PALETTE_CUSTOM": custom_names,
        "DEFAULT_PALETTE_THEME": default_theme,
    }


@lru_cache(maxsize=1)
def load_vendored_iterm_palettes() -> dict[str, dict[str, str]]:
    """Load the vendored iTerm2 palette snapshot."""
    resource = resources.files("simplex.theme").joinpath("palette_data", "iterm2.json")
    data = json.loads(resource.read_text(encoding="utf-8"))
    return {
        str(name): {str(k): _normalize_hex(str(v)) for k, v in values.items()}
        for name, values in data.items()
    }


def load_custom_palettes(
    directory: Path,
) -> tuple[dict[str, dict[str, str]], dict[str, dict[str, Any]]]:
    """Return ``(iterm_palettes, exported_palettes)`` from a custom directory."""
    ansi: dict[str, dict[str, str]] = {}
    direct: dict[str, dict[str, Any]] = {}
    if not directory.is_dir():
        return ansi, direct

    for path in sorted(directory.glob("*.itermcolors")):
        try:
            ansi[path.stem] = _load_itermcolors(path)
        except (OSError, plistlib.InvalidFileException, KeyError, TypeError, ValueError):
            continue
    for path in sorted(directory.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                direct[path.stem] = data
        except (OSError, json.JSONDecodeError, UnicodeDecodeError):
            continue
    return ansi, direct


def _load_simplex_light_export() -> dict[str, Any]:
    resource = resources.files("simplex.theme").joinpath("palette_data", "simplex_light.json")
    data = json.loads(resource.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("simplex_light palette data must be a JSON object")
    return data


def _load_itermcolors(path: Path) -> dict[str, str]:
    with path.open("rb") as file:
        raw = plistlib.load(file)
    return _iterm_colors(raw)


def _iterm_colors(theme_dict: Mapping[str, object]) -> dict[str, str]:
    colors: dict[str, str] = {}
    for key, value in theme_dict.items():
        if isinstance(value, Mapping) and "Red Component" in value:
            colors[str(key)] = _rgb_dict_to_hex(value)
    return colors


def _palette_from_export(name: str, data: Mapping[str, Any]) -> ManimPalette:
    raw_colors = data.get("manim_colors", {})
    if not isinstance(raw_colors, Mapping):
        raw_colors = {}
    colors = {str(key): _normalize_hex(str(value)) for key, value in raw_colors.items()}
    _add_color_aliases(colors)
    background = _normalize_hex(str(data.get("background_color") or colors.get("BLACK", "#000000")))
    return ManimPalette(name, background, colors)


def _palette_from_iterm(name: str, data: Mapping[str, str]) -> ManimPalette:
    colors: dict[str, str] = {}
    for base, (_, ansi_index) in _MANIM_FAMILIES.items():
        base_color = _ansi(data, ansi_index)
        for role, (kind, amount) in _SHADE_TRANSFORMS.items():
            key = f"{base}_{role}"
            colors[key] = _transform(base_color, kind, amount)
        colors[base] = colors[f"{base}_C"]

    gray_base = _ansi(data, 8)
    for role, (kind, amount) in _SHADE_TRANSFORMS.items():
        colors[f"GRAY_{role}"] = _transform(gray_base, kind, amount)
        colors[f"GREY_{role}"] = colors[f"GRAY_{role}"]
    colors["GRAY"] = colors["GREY"] = colors["GRAY_C"]
    colors["WHITE"] = _ansi(data, 7)
    colors["BLACK"] = _ansi(data, 0)
    colors["PINK"] = _ansi(data, 5)
    colors["LIGHT_PINK"] = _ansi(data, 13)
    orange = _mix(_ansi(data, 1), _ansi(data, 3), 0.5)
    colors["ORANGE"] = orange
    colors["LIGHT_BROWN"] = _lighter(orange, 0.1)
    colors["DARK_BROWN"] = _darker(orange, 0.1)
    colors["GRAY_BROWN"] = _mix(colors["LIGHT_BROWN"], _ansi(data, 8), 0.5)
    colors["GREY_BROWN"] = colors["GRAY_BROWN"]
    colors["DARK_BLUE"] = colors.get("BLUE_E", colors["BLUE"])
    background = _normalize_hex(data.get("Background Color", "#000000"))
    return ManimPalette(name, background, colors)


def _json_palette_to_swatches(data: Mapping[str, Any]) -> dict[str, str]:
    palette = _palette_from_export(str(data.get("based_on_theme") or "custom"), data)
    return _colors_to_swatches(palette.colors, palette.background)


def _colors_to_swatches(colors: Mapping[str, str], background: str) -> dict[str, str]:
    out: dict[str, str] = {"background": _normalize_hex(background)}
    for base, (group, _) in _MANIM_FAMILIES.items():
        for role in ("A", "B", "C", "D", "E"):
            value = colors.get(f"{base}_{role}")
            if value:
                out[f"{group}_{role.lower()}"] = _normalize_hex(value)
    for role in ("A", "B", "C", "D", "E"):
        value = colors.get(f"GRAY_{role}") or colors.get(f"GREY_{role}")
        if value:
            out[f"gray_{role.lower()}"] = _normalize_hex(value)
    simple = {
        "white": "WHITE",
        "black": "BLACK",
        "pink": "PINK",
        "light_pink": "LIGHT_PINK",
        "orange": "ORANGE",
        "light_brown": "LIGHT_BROWN",
        "dark_brown": "DARK_BROWN",
    }
    for swatch_id, key in simple.items():
        if value := colors.get(key):
            out[swatch_id] = _normalize_hex(value)
    if value := colors.get("GRAY_BROWN") or colors.get("GREY_BROWN"):
        out["gray_brown"] = _normalize_hex(value)
    return out


def _add_color_aliases(colors: dict[str, str]) -> None:
    for base in _MANIM_FAMILIES:
        if f"{base}_C" in colors:
            colors.setdefault(base, colors[f"{base}_C"])
    for role in ("A", "B", "C", "D", "E"):
        if f"GRAY_{role}" in colors:
            colors.setdefault(f"GREY_{role}", colors[f"GRAY_{role}"])
        if f"GREY_{role}" in colors:
            colors.setdefault(f"GRAY_{role}", colors[f"GREY_{role}"])
    if "GRAY_C" in colors:
        colors.setdefault("GRAY", colors["GRAY_C"])
        colors.setdefault("GREY", colors["GRAY_C"])
    if "GREY_C" in colors:
        colors.setdefault("GRAY", colors["GREY_C"])
        colors.setdefault("GREY", colors["GREY_C"])
    if "GRAY_BROWN" in colors:
        colors.setdefault("GREY_BROWN", colors["GRAY_BROWN"])
    if "GREY_BROWN" in colors:
        colors.setdefault("GRAY_BROWN", colors["GREY_BROWN"])
    if "BLUE_E" in colors:
        colors.setdefault("DARK_BLUE", colors["BLUE_E"])


def _ansi(data: Mapping[str, str], index: int) -> str:
    return _normalize_hex(data.get(f"Ansi {index} Color", "#000000"))


def _transform(hex_color: str, kind: str, amount: float) -> str:
    if kind == "lighter":
        return _lighter(hex_color, amount)
    if kind == "darker":
        return _darker(hex_color, amount)
    return _normalize_hex(hex_color)


def _lighter(hex_color: str, amount: float) -> str:
    return _mix(hex_color, "#FFFFFF", amount)


def _darker(hex_color: str, amount: float) -> str:
    return _mix(hex_color, "#000000", amount)


def _mix(a: str, b: str, amount: float) -> str:
    ar, ag, ab = _hex_to_rgb(a)
    br, bg, bb = _hex_to_rgb(b)
    return _rgb_to_hex(
        ar * (1 - amount) + br * amount,
        ag * (1 - amount) + bg * amount,
        ab * (1 - amount) + bb * amount,
    )


def _rgb_dict_to_hex(data: Mapping[str, object]) -> str:
    return _rgb_to_hex(
        _rgb_component(data, "Red Component") * 255,
        _rgb_component(data, "Green Component") * 255,
        _rgb_component(data, "Blue Component") * 255,
    )


def _rgb_component(data: Mapping[str, object], key: str) -> float:
    value = data[key]
    if not isinstance(value, int | float):
        raise TypeError(f"{key} must be numeric")
    return float(value)


def _hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = _normalize_hex(value).lstrip("#")
    return int(value[:2], 16), int(value[2:4], 16), int(value[4:6], 16)


def _rgb_to_hex(r: float, g: float, b: float) -> str:
    return f"#{_clamp(r):02X}{_clamp(g):02X}{_clamp(b):02X}"


def _clamp(value: float) -> int:
    return max(0, min(255, round(value)))


def _normalize_hex(value: str) -> str:
    value = value.strip()
    if not value:
        return value
    if re.fullmatch(r"#(?:[0-9a-fA-F]{6})", value):
        return value.upper()
    if re.fullmatch(r"(?:[0-9a-fA-F]{6})", value):
        return f"#{value.upper()}"
    match = re.search(r"#(?:[0-9a-fA-F]{6})", value)
    if match:
        return match.group(0).upper()
    return value
