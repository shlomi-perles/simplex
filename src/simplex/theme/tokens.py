"""Frozen Pydantic theme tokens."""

import ast
from collections.abc import Mapping
from functools import cache
from importlib.metadata import PackageNotFoundError, distribution
from pathlib import Path
from typing import Any, Final, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator
from pygments.style import Style

from simplex.theme.palettes import MANIM_DEFAULT, web_palette_for

_DEFAULT_WEB_COLORS = web_palette_for(MANIM_DEFAULT)
_MANIM_CONSTANTS = "manim/constants.py"
_MANIM_TEXT_MOBJECT = "manim/mobject/text/text_mobject.py"
_MANIM_CODE_MOBJECT = "manim/mobject/text/code_mobject.py"


# Do not import Manim here: Manim imports Simplex while discovering plugins.
# Read installed Manim source metadata to avoid that activation cycle.
@cache
def _manim_source_tree(relative_path: str) -> ast.Module:
    try:
        source_path = Path(str(distribution("manim").locate_file(relative_path)))
    except PackageNotFoundError as exc:
        raise RuntimeError("Simplex requires Manim to resolve typography defaults.") from exc
    return ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))


def _literal(value: ast.expr, context: str) -> object:
    try:
        return ast.literal_eval(value)
    except (SyntaxError, ValueError) as exc:
        raise RuntimeError(f"Could not read Manim default for {context}.") from exc


def _manim_constant(name: str) -> object:
    for node in _manim_source_tree(_MANIM_CONSTANTS).body:
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == name:
                return _literal(node.value, name)
    raise RuntimeError(f"Manim constant {name!r} was not found.")


def _manim_init_default(relative_path: str, class_name: str, parameter: str) -> object:
    for node in _manim_source_tree(relative_path).body:
        if not isinstance(node, ast.ClassDef) or node.name != class_name:
            continue
        for member in node.body:
            if not isinstance(member, ast.FunctionDef) or member.name != "__init__":
                continue
            positional = [*member.args.posonlyargs, *member.args.args]
            defaulted = positional[len(positional) - len(member.args.defaults) :]
            for arg, default in zip(defaulted, member.args.defaults, strict=True):
                if arg.arg == parameter:
                    return _literal(default, f"{class_name}.{parameter}")
            for arg, kw_default in zip(
                member.args.kwonlyargs,
                member.args.kw_defaults,
                strict=True,
            ):
                if arg.arg == parameter and kw_default is not None:
                    return _literal(kw_default, f"{class_name}.{parameter}")
    raise RuntimeError(f"Manim default {class_name}.{parameter} was not found.")


def _manim_class_attr(relative_path: str, class_name: str, attr_name: str) -> object:
    for node in _manim_source_tree(relative_path).body:
        if not isinstance(node, ast.ClassDef) or node.name != class_name:
            continue
        for member in node.body:
            if (
                isinstance(member, ast.AnnAssign)
                and isinstance(member.target, ast.Name)
                and member.target.id == attr_name
                and member.value is not None
            ):
                return _literal(member.value, f"{class_name}.{attr_name}")
            if not isinstance(member, ast.Assign):
                continue
            for target in member.targets:
                if isinstance(target, ast.Name) and target.id == attr_name:
                    return _literal(member.value, f"{class_name}.{attr_name}")
    raise RuntimeError(f"Manim class attribute {class_name}.{attr_name} was not found.")


def _manim_default_font_size() -> int:
    font_size = _manim_constant("DEFAULT_FONT_SIZE")
    if not isinstance(font_size, int):
        raise RuntimeError("Manim DEFAULT_FONT_SIZE must be an integer.")
    return font_size


def _manim_text_font_default() -> str:
    font = _manim_init_default(_MANIM_TEXT_MOBJECT, "Text", "font")
    if not isinstance(font, str):
        raise RuntimeError("Manim Text.font default must be a string.")
    return font


def _manim_code_font_default() -> str:
    paragraph_config = _manim_class_attr(
        _MANIM_CODE_MOBJECT,
        "Code",
        "default_paragraph_config",
    )
    if not isinstance(paragraph_config, dict) or not isinstance(
        font := paragraph_config.get("font"),
        str,
    ):
        raise RuntimeError("Manim Code.default_paragraph_config['font'] must be a string.")
    return font


_MANIM_DEFAULT_FONT_SIZE: Final[int] = _manim_default_font_size()
_MANIM_DEFAULT_FONT_FAMILY: Final[str] = _manim_text_font_default()
_MANIM_DEFAULT_MONO_FAMILY: Final[str] = _manim_code_font_default()


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
    font_family: str = _MANIM_DEFAULT_FONT_FAMILY
    mono_family: str = _MANIM_DEFAULT_MONO_FAMILY
    body: int = _MANIM_DEFAULT_FONT_SIZE
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
