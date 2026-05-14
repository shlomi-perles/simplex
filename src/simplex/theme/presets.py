"""Preset Theme instances seeded from Dastimator's consts.py."""

from simplex.theme.tokens import LatexProfile, Palette, Theme, Typography

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
