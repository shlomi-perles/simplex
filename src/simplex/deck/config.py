"""DeckConfig -- pydantic model loaded from each deck's deck.toml.

The canonical scene list is a single ordered ``entrypoints`` array:

- ``"slides.intro:Title"`` renders with Cairo unless the source file declares
  a file-level renderer.
- ``"slides.surface:Surface@opengl"`` pins one scene to ManimCE's OpenGL
  renderer.

``section_slug`` is populated by the registry, not the author.

Three nested override types tune per-deck or per-main-slide behaviour:

- ``SlideOverride`` -- per-main-slide tweaks (thumbnail path/index, notes
  anchor, order). Keyed by the main slide's ``name=`` in ``deck.slides``.
- ``WebOverride`` -- per-deck portal + RevealJS palette overrides
  (``deck.web``). Every field is optional; ``resolved_web_palette()``
  merges with the active theme's defaults field-by-field.
"""

import ast
import re
import tomllib
from datetime import date
from pathlib import Path
from typing import Literal, NamedTuple, Self

from pydantic import BaseModel, ConfigDict, field_validator, model_validator
from pygments.style import Style

from simplex.theme.presets import get as get_theme
from simplex.theme.tokens import WebPalette

_SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_ENTRYPOINT = re.compile(r"^[A-Za-z_][\w.]*:[A-Za-z_]\w*$")
type RendererName = Literal["cairo", "opengl"]


class ResolvedSceneGroup(NamedTuple):
    """A renderable batch of scene classes sharing one source file and renderer."""

    source_file: Path
    scene_names: tuple[str, ...]
    renderer: RendererName


class SceneEntrypoint(BaseModel):
    """One scene class entrypoint, optionally pinned to a ManimCE renderer."""

    model_config = ConfigDict(frozen=True)
    target: str
    renderer: RendererName | None = None

    @field_validator("target")
    @classmethod
    def _target_format(cls, value: str) -> str:
        if not _ENTRYPOINT.match(value):
            raise ValueError(f"entrypoint must be 'module[.sub]:ClassName', got {value!r}")
        return value

    @field_validator("renderer", mode="before")
    @classmethod
    def _renderer_format(cls, value: object) -> object:
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValueError("renderer must be 'cairo' or 'opengl'")
        renderer = value.lower()
        if renderer not in {"cairo", "opengl"}:
            raise ValueError("renderer must be 'cairo' or 'opengl'")
        return renderer


class SlideOverride(BaseModel):
    """Per-main-slide override. Keyed by the ``name=`` passed to next_slide."""

    model_config = ConfigDict(frozen=True)
    thumbnail: Path | None = None
    thumbnail_section_index: int = -2
    notes_anchor: str | None = None
    order_override: float | None = None


class WebOverride(BaseModel):
    """Per-deck portal + RevealJS overrides. Every field is optional.

    Resolution: ``deck.web`` field if non-None > ``theme.web_palette`` field >
    ``WebPalette()`` default. RevealJS-specific fields (``transition``,
    ``controls``, ...) are passed straight to the converter.
    """

    model_config = ConfigDict(frozen=True)
    accent: str | None = None
    background: str | None = None
    surface: str | None = None
    text_primary: str | None = None
    text_muted: str | None = None
    link: str | None = None
    code_background: str | None = None
    font_family_sans: str | None = None
    font_family_mono: str | None = None
    font_size_base: str | None = None

    # RevealJS knobs (forwarded to manim_slides.convert.RevealJS kwargs).
    # Default ``"none"``: the next video replaces the previous one with no
    # animation. This keeps both desktop and mobile playback direction-free.
    transition: str = "none"
    controls: bool = True
    progress: bool = True
    hash_navigation: bool = True

    # Slide-presentation chrome. These used to be drawn into each frame
    # by ``make_chrome(..., page=)``; they now live in the RevealJS host
    # so toggling them is free (no re-render).
    show_slide_number: bool = False
    show_clock: bool = False
    show_stopwatch: bool = False
    notes_code_style: str | None = None

    # Homepage/section carousel preview. ``carousel_gif`` points to a
    # user-authored GIF relative to the deck directory. When omitted,
    # ``carousel_gif_slides`` can select 1-based main-slide indexes to
    # synthesize a small progressive preview from rendered video segments.
    carousel_gif: Path | None = None
    carousel_gif_slides: tuple[int, ...] = ()

    @field_validator("carousel_gif_slides")
    @classmethod
    def _carousel_gif_slides_positive(cls, value: tuple[int, ...]) -> tuple[int, ...]:
        if any(i < 1 for i in value):
            raise ValueError("carousel_gif_slides uses 1-based slide indexes")
        return value

    # Escape hatches.
    custom_css_path: Path | None = None
    template: Path | None = None


class DeckConfig(BaseModel):
    model_config = ConfigDict(frozen=True)
    slug: str
    title: str
    summary: str = ""
    tags: tuple[str, ...] = ()
    theme: str = "simplex_dark"
    scenes: tuple[str, ...] = ()
    entrypoints: tuple[SceneEntrypoint, ...] = ()
    quality: str = "high_quality"
    voiceover: bool = False
    category: str | None = None
    duration_minutes: int | None = None
    created_at: date | None = None
    order: int = 1000
    path: Path
    section_slug: str = "featured"

    # v0.2 additions.
    caching: bool = True
    self_test: bool = False
    render_quality_dev: str = "low_quality"
    render_quality_release: str = "high_quality"
    slides: dict[str, SlideOverride] = {}
    slide_order: tuple[str, ...] = ()
    web: WebOverride = WebOverride()

    @field_validator("slug")
    @classmethod
    def _slug_format(cls, value: str) -> str:
        if not _SLUG.match(value):
            raise ValueError(f"slug must be kebab-case (a-z0-9 with single hyphens), got {value!r}")
        return value

    @field_validator("entrypoints", mode="before")
    @classmethod
    def _entrypoint_format(cls, value: object) -> object:
        if value is None:
            return ()
        if isinstance(value, tuple | list):
            return [_parse_entrypoint_item(item) for item in value]
        return value

    @model_validator(mode="after")
    def _at_least_one_scene_source(self) -> Self:
        return self

    @property
    def scene_specs(self) -> tuple[str, ...]:
        """Return entrypoints if present, else ``slides.py``-relative scenes."""
        return tuple(ep.target for ep in self.scene_entrypoints)

    @property
    def scene_entrypoints(self) -> tuple[SceneEntrypoint, ...]:
        """Return normalized scene entrypoints."""
        if self.entrypoints:
            return self.entrypoints
        return tuple(SceneEntrypoint(target=f"slides:{name}") for name in self.scenes)

    @property
    def scene_class_names(self) -> tuple[str, ...]:
        """Bare class names extracted from ``scene_specs``."""
        return tuple(spec.rsplit(":", 1)[-1] for spec in self.scene_specs)

    def resolve_entrypoints(self) -> tuple[ResolvedSceneGroup, ...]:
        """Group entrypoints by source file and resolved renderer."""
        groups: dict[tuple[Path, RendererName], list[str]] = {}
        source_renderers: dict[Path, RendererName | None] = {}
        for entrypoint in self.scene_entrypoints:
            module, _, class_name = entrypoint.target.partition(":")
            file_path = self._module_to_file(module)
            source_renderer = source_renderers.setdefault(
                file_path,
                detect_source_renderer(file_path),
            )
            if (
                entrypoint.renderer is not None
                and source_renderer is not None
                and entrypoint.renderer != source_renderer
            ):
                raise ValueError(
                    f"deck {self.slug!r}: entrypoint {entrypoint.target!r} declares "
                    f"renderer={entrypoint.renderer!r}, but {file_path} sets "
                    f"config.renderer={source_renderer!r}"
                )
            renderer = entrypoint.renderer or source_renderer or "cairo"
            groups.setdefault((file_path, renderer), []).append(class_name)
        return tuple(
            ResolvedSceneGroup(source_file=file_path, scene_names=tuple(names), renderer=renderer)
            for (file_path, renderer), names in groups.items()
        )

    def resolved_web_palette(self) -> WebPalette:
        """Merge per-deck ``web`` overrides over the active theme's palette.

        Returns a fully-resolved ``WebPalette`` (every field set). Used by
        the web builder + RevealJS template injection.
        """
        theme = get_theme(self.theme)
        base = theme.web_palette
        web = self.web
        return WebPalette(
            accent=web.accent or base.accent,
            background=web.background or base.background,
            surface=web.surface or base.surface,
            text_primary=web.text_primary or base.text_primary,
            text_muted=web.text_muted or base.text_muted,
            link=web.link or base.link,
            code_background=web.code_background or base.code_background,
            font_family_sans=web.font_family_sans or base.font_family_sans,
            font_family_mono=web.font_family_mono or base.font_family_mono,
            font_size_base=web.font_size_base or base.font_size_base,
        )

    def resolved_code_style(self) -> type[Style]:
        """Return the Pygments style class for this deck's theme."""
        theme = get_theme(self.theme)
        style: type[Style] | None = getattr(theme, "code_style", None)
        if style is not None:
            return style
        mod = __import__("simplex.theme.pygments_style", fromlist=["SimplexPycharm"])
        return mod.SimplexPycharm  # type: ignore[no-any-return]

    def resolved_notes_code_style(self) -> type[Style]:
        """Return the Pygments style class for markdown notes code blocks."""
        from simplex.theme.pygments_style import resolve_style
        from simplex.theme.styles.simplex_solarized_light import SimplexSolarizedLight

        return resolve_style(self.web.notes_code_style, default=SimplexSolarizedLight)

    def _module_to_file(self, module: str) -> Path:
        """Map ``slides.foo.bar`` to the deck-relative ``.py`` file."""
        parts = module.split(".")
        module_path = self.path.joinpath(*parts)
        as_file = module_path.with_suffix(".py")
        if as_file.exists():
            return as_file
        as_pkg = module_path / "__init__.py"
        if as_pkg.exists():
            return as_pkg
        raise FileNotFoundError(
            f"deck {self.slug!r}: entrypoint module {module!r} resolves to neither "
            f"{as_file} nor {as_pkg}"
        )

    @classmethod
    def load(cls, deck_dir: Path, *, section_slug: str = "featured") -> Self:
        toml_path = deck_dir / "deck.toml"
        data = tomllib.loads(toml_path.read_text(encoding="utf-8"))
        return cls(**data, path=deck_dir, section_slug=section_slug)


def _parse_entrypoint_item(value: object) -> object:
    if not isinstance(value, str):
        return value
    target, separator, renderer = value.rpartition("@")
    if not separator:
        return {"target": value}
    return {"target": target, "renderer": renderer}


def detect_source_renderer(source_file: Path) -> RendererName | None:
    """Read simple top-level ``config.renderer = "..."`` assignments.

    This preserves Manim-style file-level renderer opt-in for standalone scene
    authoring while letting deck metadata remain the preferred source of truth.
    """
    try:
        tree = ast.parse(source_file.read_text(encoding="utf-8"), filename=str(source_file))
    except (OSError, SyntaxError, UnicodeDecodeError):
        return None

    renderer: RendererName | None = None
    for node in tree.body:
        if isinstance(node, ast.Assign):
            if any(_is_config_renderer_target(target) for target in node.targets):
                renderer = _renderer_literal(node.value) or renderer
        elif isinstance(node, ast.AnnAssign) and _is_config_renderer_target(node.target):
            renderer = _renderer_literal(node.value) or renderer
    return renderer


def _is_config_renderer_target(target: ast.AST) -> bool:
    if isinstance(target, ast.Attribute):
        return (
            isinstance(target.value, ast.Name)
            and target.value.id == "config"
            and target.attr == "renderer"
        )
    if isinstance(target, ast.Subscript):
        return (
            isinstance(target.value, ast.Name)
            and target.value.id == "config"
            and isinstance(target.slice, ast.Constant)
            and target.slice.value == "renderer"
        )
    return False


def _renderer_literal(value: ast.AST | None) -> RendererName | None:
    if not isinstance(value, ast.Constant) or not isinstance(value.value, str):
        return None
    renderer = value.value.lower()
    if renderer == "cairo":
        return "cairo"
    if renderer == "opengl":
        return "opengl"
    return None
