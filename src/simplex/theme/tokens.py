"""Frozen Pydantic theme tokens."""

from collections.abc import Mapping
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator
from pygments.style import Style

from simplex.theme.palettes import MANIM_DEFAULT, web_palette_for

_DEFAULT_WEB_COLORS = web_palette_for(MANIM_DEFAULT)


type ThemeVariant = Literal["dark", "light"]


class Palette(BaseModel):
    """Semantic video colors.

    ``edge`` is reserved for the graph ``Edge`` mobject; ordinary Manim
    strokes use Manim's ``WHITE`` constant after the theme palette is applied.
    """

    model_config = ConfigDict(frozen=True, extra="allow")
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
    """Layout constants for slide chrome and Mobject strokes.

    The ``*_buff`` fields are the inward gap between a chrome mobject (header,
    footer) and the corresponding edge of the slide region — i.e. the ``buff``
    argument forwarded to :meth:`Region.place`. Themes override per slide-deck.
    ``edge_stroke_width`` is reserved for the graph ``Edge`` mobject.
    """

    model_config = ConfigDict(frozen=True)
    edge_stroke_width: float = 6.0
    vertex_stroke_width: float = 6.4
    page_margin: float = 0.4
    header_height: float = 0.7
    footer_height: float = 0.5
    header_buff: float = 0.15
    footer_buff: float = 0.2


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
    """CSS variables for the generated portal and deck player pages.

    Each field maps to a ``--simplex-*`` CSS custom property emitted by
    ``simplex.theme.web_css.render_web_css``. Decks override individual
    fields via ``[web]`` in ``deck.toml``; unset fields fall back to the
    theme's defaults.
    """

    model_config = ConfigDict(frozen=True)
    accent: str = _DEFAULT_WEB_COLORS["accent"]
    background: str = "#2b2b2b"
    surface: str = "#2D2D2D"
    text_primary: str = _DEFAULT_WEB_COLORS["text_primary"]
    text_muted: str = "#A0A0A0"
    link: str = _DEFAULT_WEB_COLORS["link"]
    font_family_sans: str = "system-ui, sans-serif"
    font_family_mono: str = "'JetBrains Mono', monospace"
    font_size_base: str = "1rem"


class Theme(BaseModel):
    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)
    name: str
    variant: ThemeVariant | None = None
    manim_palette: str | None = None
    palette: Palette
    typography: Typography = Field(default_factory=Typography)
    spacing: Spacing = Field(default_factory=Spacing)
    motion: Motion = Field(default_factory=Motion)
    latex: LatexProfile = Field(default_factory=LatexProfile)
    web_palette: WebPalette = Field(default_factory=WebPalette)
    code_style: type[Style] = Field(default=None)  # type: ignore[assignment]

    @model_validator(mode="before")
    @classmethod
    def _derive_palette_defaults(cls, data: object) -> object:
        if not isinstance(data, dict):
            return data

        values = dict(data)
        if isinstance(values.get("code_style"), str):
            from simplex.theme.pygments_style import resolve_style
            from simplex.theme.styles.simplex_pycharm import SimplexPycharm

            values["code_style"] = resolve_style(values["code_style"], default=SimplexPycharm)
        variant = _theme_variant(values.get("variant"))
        palette_name = values.get("manim_palette")
        raw_palette = values.get("palette")
        explicit_palette = _resolve_variant_values(_model_or_mapping(raw_palette), variant)
        if raw_palette is not None:
            values["palette"] = explicit_palette
        missing_palette = raw_palette is None or not set(Palette.model_fields).issubset(
            explicit_palette
        )
        if missing_palette:
            from simplex.theme.palettes import MANIM_DEFAULT, semantic_palette_for

            derived = semantic_palette_for(str(palette_name or MANIM_DEFAULT))
            values["palette"] = derived | {
                key: value for key, value in explicit_palette.items() if value is not None
            }

        raw_web = values.get("web_palette")
        explicit_web = _resolve_variant_values(_model_or_mapping(raw_web), variant)
        if raw_web is not None:
            values["web_palette"] = explicit_web
        if raw_web is None or isinstance(raw_web, dict | WebPalette):
            from simplex.theme.palettes import MANIM_DEFAULT, web_palette_for

            derived_web = web_palette_for(str(palette_name or MANIM_DEFAULT))
            resolved_palette = _model_or_mapping(values.get("palette"))
            if isinstance(background := resolved_palette.get("background"), str):
                derived_web["background"] = background
            if isinstance(font := resolved_palette.get("font"), str):
                derived_web["text_primary"] = font
            if isinstance(accent := resolved_palette.get("accent"), str):
                derived_web["accent"] = accent
                derived_web["link"] = accent
            values["web_palette"] = derived_web | {
                key: value for key, value in explicit_web.items() if value is not None
            }

        return values

    def __init__(self, **data: Any) -> None:
        if data.get("code_style") is None:
            from simplex.theme.styles.simplex_pycharm import SimplexPycharm

            data["code_style"] = SimplexPycharm
        super().__init__(**data)


def _model_or_mapping(value: object) -> dict[str, object]:
    if isinstance(value, BaseModel):
        return value.model_dump()
    if isinstance(value, Mapping):
        return dict(value)
    return {}


def _theme_variant(value: object) -> ThemeVariant | None:
    if value in {"dark", "light"}:
        return value  # type: ignore[return-value]
    return None


def _resolve_variant_values(
    values: dict[str, object],
    variant: ThemeVariant | None,
) -> dict[str, object]:
    """Resolve ``{"light": ..., "dark": ...}`` palette values.

    The true slide-theme role is the source of truth. When a theme is loaded
    outside that context, dark is the conservative default because it matches
    Simplex's package default.
    """
    if not values:
        return values
    selected = variant or "dark"
    fallback = "light" if selected == "dark" else "dark"
    resolved: dict[str, object] = {}
    for key, value in values.items():
        if isinstance(value, Mapping) and ("light" in value or "dark" in value):
            if selected in value:
                resolved[key] = value[selected]
            elif fallback in value:
                resolved[key] = value[fallback]
            else:
                resolved[key] = value
            continue
        resolved[key] = value
    return resolved
