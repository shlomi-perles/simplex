"""Frozen Pydantic theme tokens."""

from collections.abc import Mapping
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class Palette(BaseModel):
    model_config = ConfigDict(frozen=True)
    background: str
    font: str
    accent: str
    vertex: str
    vertex_stroke: str
    edge: str
    weight: str
    visited: str
    label: str
    distance: str


class Typography(BaseModel):
    model_config = ConfigDict(frozen=True)
    font_family: str = "sans-serif"
    mono_family: str = "monospace"
    body: int = 30
    h1: int = 60
    h2: int = 48
    caption: int = 20


class Spacing(BaseModel):
    model_config = ConfigDict(frozen=True)
    edge_stroke_width: float = 6.0
    vertex_stroke_width: float = 6.4
    page_margin: float = 0.4
    header_height: float = 0.7
    footer_height: float = 0.5


class Motion(BaseModel):
    model_config = ConfigDict(frozen=True)
    transition_duration: float = 0.5
    emphasis_duration: float = 0.8


class LatexProfile(BaseModel):
    model_config = ConfigDict(frozen=True)
    extra_packages: tuple[str, ...] = ()
    preamble: str = ""
    environments: Mapping[str, str] = Field(default_factory=dict)
    tex_compiler: str = "latex"

    def as_tex_template(self) -> Any:
        from manim import TexTemplate

        tmpl = TexTemplate(tex_compiler=self.tex_compiler)
        for pkg in self.extra_packages:
            tmpl.add_to_preamble(rf"\usepackage{{{pkg}}}")
        if self.preamble:
            tmpl.add_to_preamble(self.preamble)
        return tmpl


class WebPalette(BaseModel):
    """CSS variables for the generated portal + RevealJS deck pages.

    Each field maps to a ``--simplex-*`` CSS custom property emitted by
    ``simplex.theme.web_css.render_web_css``. Decks override individual
    fields via ``[web]`` in ``deck.toml``; unset fields fall back to the
    theme's defaults.
    """

    model_config = ConfigDict(frozen=True)
    accent: str = "#FFD700"
    background: str = "#242424"
    surface: str = "#2D2D2D"
    text_primary: str = "#FFFFFF"
    text_muted: str = "#A0A0A0"
    link: str = "#58C4DD"
    code_background: str = "#111111"
    font_family_sans: str = "system-ui, sans-serif"
    font_family_mono: str = "'JetBrains Mono', monospace"
    font_size_base: str = "1rem"


class Theme(BaseModel):
    model_config = ConfigDict(frozen=True)
    name: str
    palette: Palette
    typography: Typography = Field(default_factory=Typography)
    spacing: Spacing = Field(default_factory=Spacing)
    motion: Motion = Field(default_factory=Motion)
    latex: LatexProfile = Field(default_factory=LatexProfile)
    web_palette: WebPalette = Field(default_factory=WebPalette)
