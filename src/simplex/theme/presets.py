"""Preset and project-local Simplex theme instances."""

import json

from simplex.theme.styles.simplex_pycharm import SimplexPycharm
from simplex.theme.styles.simplex_solarized_light import SimplexSolarizedLight
from simplex.theme.tokens import LatexProfile, Palette, Theme, Typography, WebPalette

_COMPACT_DISPLAY_PREAMBLE = (
    r"\setlength{\abovedisplayskip}{0pt}"
    "\n"
    r"\setlength{\belowdisplayskip}{0pt}"
    "\n"
    r"\setlength{\abovedisplayshortskip}{0pt}"
    "\n"
    r"\setlength{\belowdisplayshortskip}{0pt}"
    "\n"
)

SIMPLEX_DARK: Theme = Theme(
    name="simplex_dark",
    manim_palette="manim_default",
    palette=Palette(
        background="#242424",
        font="#FFFFFF",
        accent="#FFD700",
        vertex="#236B8E",
        vertex_stroke="#58C4DD",
        edge="#FFFFFF",
        weight="#F4D345",
        visited="#00FF00",
        label="#FFFFFF",
        distance="#FF8000",
    ),
    typography=Typography(mono_family="JetBrains Mono"),
    latex=LatexProfile(preamble=_COMPACT_DISPLAY_PREAMBLE),
    web_palette=WebPalette(
        accent="#FFD700",
        background="#2b2b2b",
        surface="#2D2D2D",
        text_primary="#FFFFFF",
        text_muted="#A0A0A0",
        link="#58C4DD",
        font_family_sans="system-ui, -apple-system, sans-serif",
        font_family_mono="'JetBrains Mono', 'Fira Code', monospace",
        font_size_base="1rem",
    ),
    code_style=SimplexPycharm,
)

SIMPLEX_LIGHT: Theme = Theme(
    name="simplex_light",
    manim_palette="simplex_light",
    typography=Typography(mono_family="JetBrains Mono"),
    latex=LatexProfile(preamble=_COMPACT_DISPLAY_PREAMBLE),
    code_style=SimplexSolarizedLight,
)

PRESETS: dict[str, Theme] = {
    SIMPLEX_DARK.name: SIMPLEX_DARK,
    SIMPLEX_LIGHT.name: SIMPLEX_LIGHT,
}


def get(name: str) -> Theme:
    """Return a built-in or repo-local custom theme by name."""
    if name in PRESETS:
        return PRESETS[name]
    if theme := _load_custom_theme(name):
        return theme
    known = ", ".join(available_names())
    raise KeyError(f"unknown theme {name!r}; known: {known}")


def available_names() -> tuple[str, ...]:
    """Return built-in and project-local custom theme names."""
    from simplex.theme.palettes import theme_styles_dir

    names = set(PRESETS)
    directory = theme_styles_dir()
    if directory.is_dir():
        names.update(path.stem for path in directory.glob("*.json"))
    return tuple(sorted(names))


def _load_custom_theme(name: str) -> Theme | None:
    from simplex.theme.palettes import theme_styles_dir

    path = theme_styles_dir() / f"{name}.json"
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"theme file {path} must contain a JSON object")
    values = dict(data)
    values["name"] = name
    return Theme(**values)
