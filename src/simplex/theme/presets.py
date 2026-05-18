"""Preset Theme instances seeded from Dastimator's consts.py."""

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

DASTIMATOR_DARK: Theme = Theme(
    name="dastimator_dark",
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
    latex=LatexProfile(
        preamble=_COMPACT_DISPLAY_PREAMBLE,
        environments={"definition": "{minipage}{8cm}"},
    ),
    web_palette=WebPalette(
        accent="#FFD700",
        background="#242424",
        surface="#2D2D2D",
        text_primary="#FFFFFF",
        text_muted="#A0A0A0",
        link="#58C4DD",
        code_background="#111111",
        font_family_sans="system-ui, -apple-system, sans-serif",
        font_family_mono="'JetBrains Mono', 'Fira Code', monospace",
        font_size_base="1rem",
    ),
)

ACADEMIC_LIGHT: Theme = Theme(
    name="academic_light",
    palette=Palette(
        background="#FFFFFF",
        font="#1A1A1A",
        accent="#0066CC",
        vertex="#0066CC",
        vertex_stroke="#003D7A",
        edge="#1A1A1A",
        weight="#B45309",
        visited="#0F7D2F",
        label="#1A1A1A",
        distance="#B45309",
    ),
    typography=Typography(),
    latex=LatexProfile(
        environments={"definition": "{minipage}{8cm}"},
    ),
    web_palette=WebPalette(
        accent="#0066CC",
        background="#FFFFFF",
        surface="#F4F4F4",
        text_primary="#1A1A1A",
        text_muted="#6B6B6B",
        link="#0066CC",
        code_background="#F8F8F8",
        font_family_sans="system-ui, -apple-system, sans-serif",
        font_family_mono="'JetBrains Mono', 'Fira Code', monospace",
        font_size_base="1rem",
    ),
)

PRESETS: dict[str, Theme] = {
    DASTIMATOR_DARK.name: DASTIMATOR_DARK,
    ACADEMIC_LIGHT.name: ACADEMIC_LIGHT,
}


def get(name: str) -> Theme:
    try:
        return PRESETS[name]
    except KeyError as exc:
        known = ", ".join(sorted(PRESETS))
        raise KeyError(f"unknown theme {name!r}; known: {known}") from exc
