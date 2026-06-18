"""Deck discovery and TOML editing helpers for the Simplex manager."""

from __future__ import annotations

import ast
import datetime as dt
import json
import tomllib
from pathlib import Path
from typing import Literal, NotRequired, TypedDict, cast

import tomli_w

from simplex.deck.config import DeckConfig, RendererName, SceneEntrypoint, detect_source_renderer
from simplex.deck.registry import discover
from simplex.render import themes
from simplex.web.site_config import SiteConfig

CacheMode = Literal["on", "off", "flush"]
SlideThemeSelection = Literal["all", "dark", "light"]


class QualityOption(TypedDict):
    name: str
    label: str
    flag: str
    pixel_width: int
    pixel_height: int
    frame_rate: int


OptionKind = Literal[
    "string", "integer", "boolean", "date", "string_list", "integer_list", "select"
]


class DeckOptionSpec(TypedDict):
    path: str
    group: str
    label: str
    kind: OptionKind
    help: str
    required: NotRequired[bool]
    default: NotRequired[object]
    choices: NotRequired[tuple[str, ...]]
    readonly: NotRequired[bool]


class DeckOptionValue(TypedDict):
    value: object
    present: bool


_SCENE_BASE_NAMES = {
    "Scene",
    "ThreeDScene",
    "MovingCameraScene",
    "Slide",
    "ThreeDSlide",
    "BaseSlide",
    "SimplexScene",
    "SimplexThreeDScene",
    "OutlineScene",
}

_UNSET = object()

_DECK_OPTION_SPECS: tuple[DeckOptionSpec, ...] = (
    {
        "path": "slug",
        "group": "Metadata",
        "label": "Slug",
        "kind": "string",
        "required": True,
        "readonly": True,
        "help": "Stable kebab-case deck id. Rename deliberately; rendered output paths use this value.",
    },
    {
        "path": "title",
        "group": "Metadata",
        "label": "Title",
        "kind": "string",
        "required": True,
        "help": "Human-readable deck title shown in the portal and manager.",
    },
    {
        "path": "summary",
        "group": "Metadata",
        "label": "Summary",
        "kind": "string",
        "default": "",
        "help": "Short deck description. Empty uses the package default and is omitted from TOML.",
    },
    {
        "path": "tags",
        "group": "Metadata",
        "label": "Tags",
        "kind": "string_list",
        "default": (),
        "help": "Comma- or newline-separated tags for future filtering and card metadata.",
    },
    {
        "path": "category",
        "group": "Metadata",
        "label": "Category",
        "kind": "string",
        "default": None,
        "help": "Optional display category. Empty means no category field is written.",
    },
    {
        "path": "date",
        "group": "Metadata",
        "label": "Date",
        "kind": "date",
        "default": None,
        "help": "Optional publication date as YYYY-MM-DD. Empty lets Simplex infer a date.",
    },
    {
        "path": "duration_minutes",
        "group": "Metadata",
        "label": "Minutes",
        "kind": "integer",
        "default": None,
        "help": "Optional manual duration shown on cards. Empty uses rendered duration when available.",
    },
    {
        "path": "order",
        "group": "Metadata",
        "label": "Order",
        "kind": "integer",
        "default": 1000,
        "help": "Deck ordering within its section. Empty or 1000 omits the field.",
    },
    {
        "path": "self_test",
        "group": "Render",
        "label": "Self Test",
        "kind": "boolean",
        "default": False,
        "help": "Marks this deck for internal smoke-test behavior. Default is off.",
    },
    {
        "path": "theme",
        "group": "Render",
        "label": "Theme",
        "kind": "string",
        "default": "simplex_dark",
        "help": "Single-render fallback theme. Empty or simplex_dark uses the package default.",
    },
    {
        "path": "slide_theme_variant",
        "group": "Render",
        "label": "Theme Variant",
        "kind": "select",
        "choices": ("dark", "light"),
        "default": None,
        "help": "Optional fixed theme variant passed to scene code. Default inherits the active variant.",
    },
    {
        "path": "scenes",
        "group": "Render",
        "label": "Legacy Scenes",
        "kind": "string_list",
        "default": (),
        "help": "Legacy slides.py class list used only when entrypoints is empty. Prefer entrypoints.",
    },
    {
        "path": "slide_order",
        "group": "Render",
        "label": "Slide Order",
        "kind": "string_list",
        "default": (),
        "help": "Optional main-slide name order override. Empty uses render order.",
    },
    {
        "path": "slide_themes.enabled",
        "group": "Slide Themes",
        "label": "Enabled",
        "kind": "boolean",
        "default": None,
        "help": "Default inherits site/package behavior. On renders real dark/light videos; off uses one render with CSS filtering.",
    },
    {
        "path": "slide_themes.dark",
        "group": "Slide Themes",
        "label": "Dark Theme",
        "kind": "string",
        "default": None,
        "help": "Dark slide theme name. Empty inherits the site/package default.",
    },
    {
        "path": "slide_themes.light",
        "group": "Slide Themes",
        "label": "Light Theme",
        "kind": "string",
        "default": None,
        "help": "Light slide theme name. Empty inherits the site/package default.",
    },
    {
        "path": "slide_themes.default",
        "group": "Slide Themes",
        "label": "Default Variant",
        "kind": "select",
        "choices": ("dark", "light"),
        "default": None,
        "help": "Default player variant. Empty inherits the site/package default.",
    },
    {
        "path": "web.accent",
        "group": "Web",
        "label": "Accent",
        "kind": "string",
        "default": None,
        "help": "Portal/player accent color. Empty inherits from the active theme.",
    },
    {
        "path": "web.background",
        "group": "Web",
        "label": "Background",
        "kind": "string",
        "default": None,
        "help": "Portal/player background color. Empty inherits from the active theme.",
    },
    {
        "path": "web.surface",
        "group": "Web",
        "label": "Surface",
        "kind": "string",
        "default": None,
        "help": "Panel/card surface color. Empty inherits from the active theme.",
    },
    {
        "path": "web.text_primary",
        "group": "Web",
        "label": "Text",
        "kind": "string",
        "default": None,
        "help": "Primary text color. Empty inherits from the active theme.",
    },
    {
        "path": "web.text_muted",
        "group": "Web",
        "label": "Muted Text",
        "kind": "string",
        "default": None,
        "help": "Muted text color. Empty inherits from the active theme.",
    },
    {
        "path": "web.link",
        "group": "Web",
        "label": "Link",
        "kind": "string",
        "default": None,
        "help": "Link color. Empty inherits from the active theme.",
    },
    {
        "path": "web.font_family_sans",
        "group": "Web",
        "label": "Sans Font",
        "kind": "string",
        "default": None,
        "help": "CSS font-family for normal text. Empty inherits from the active theme.",
    },
    {
        "path": "web.font_family_mono",
        "group": "Web",
        "label": "Mono Font",
        "kind": "string",
        "default": None,
        "help": "CSS font-family for code text. Empty inherits from the active theme.",
    },
    {
        "path": "web.font_size_base",
        "group": "Web",
        "label": "Base Font Size",
        "kind": "string",
        "default": None,
        "help": "CSS base font size, for example 16px. Empty inherits from the active theme.",
    },
    {
        "path": "web.transition",
        "group": "Web",
        "label": "Transition",
        "kind": "string",
        "default": "none",
        "help": "Timeline-player transition policy. Empty or none uses the default.",
    },
    {
        "path": "web.controls",
        "group": "Web",
        "label": "Controls",
        "kind": "boolean",
        "default": True,
        "help": "Show player controls. Default is on.",
    },
    {
        "path": "web.progress",
        "group": "Web",
        "label": "Progress",
        "kind": "boolean",
        "default": True,
        "help": "Show player progress UI. Default is on.",
    },
    {
        "path": "web.hash_navigation",
        "group": "Web",
        "label": "Hash Nav",
        "kind": "boolean",
        "default": True,
        "help": "Allow URL hash navigation between slides. Default is on.",
    },
    {
        "path": "web.show_slide_number",
        "group": "Web",
        "label": "Slide Number",
        "kind": "boolean",
        "default": False,
        "help": "Show slide numbers in the web player shell. Default is off.",
    },
    {
        "path": "web.show_clock",
        "group": "Web",
        "label": "Clock",
        "kind": "boolean",
        "default": False,
        "help": "Show a clock in the web player shell. Default is off.",
    },
    {
        "path": "web.show_stopwatch",
        "group": "Web",
        "label": "Stopwatch",
        "kind": "boolean",
        "default": False,
        "help": "Show a stopwatch in the web player shell. Default is off.",
    },
    {
        "path": "web.show_notes_date",
        "group": "Web",
        "label": "Notes Date",
        "kind": "boolean",
        "default": False,
        "help": "Show the resolved deck date in notes. Default is off.",
    },
    {
        "path": "web.notes_code_style",
        "group": "Web",
        "label": "Notes Code Style",
        "kind": "string",
        "default": None,
        "help": "Pygments style for notes code blocks. Empty uses the package default.",
    },
    {
        "path": "web.carousel_gif",
        "group": "Web",
        "label": "Carousel GIF",
        "kind": "string",
        "default": None,
        "help": "Authored GIF path relative to the deck directory. Empty synthesizes previews when possible.",
    },
    {
        "path": "web.carousel_gif_slides",
        "group": "Web",
        "label": "GIF Slides",
        "kind": "integer_list",
        "default": (),
        "help": "1-based main-slide indexes for a synthesized carousel GIF. Empty uses defaults.",
    },
    {
        "path": "web.custom_css_path",
        "group": "Web",
        "label": "Custom CSS",
        "kind": "string",
        "default": None,
        "help": "Optional CSS file path relative to the deck directory. Empty writes no override.",
    },
    {
        "path": "web.template",
        "group": "Web",
        "label": "Template",
        "kind": "string",
        "default": None,
        "help": "Optional custom deck page template path. Empty uses the package template.",
    },
    {
        "path": "hosting.media_base_url",
        "group": "Hosting",
        "label": "Media Base URL",
        "kind": "string",
        "default": "",
        "help": "Base URL for hosted media. Empty inherits site/package behavior.",
    },
    {
        "path": "packaging.hls_segment_duration",
        "group": "Packaging",
        "label": "HLS Segment Seconds",
        "kind": "integer",
        "default": 4,
        "help": "HLS/CMAF segment duration. Empty or 4 uses the default.",
    },
    {
        "path": "packaging.strict_budgets",
        "group": "Packaging",
        "label": "Strict Budgets",
        "kind": "boolean",
        "default": False,
        "help": "Treat packaging budget warnings as stricter policy. Default is off.",
    },
    {
        "path": "packaging.warn_site_bytes",
        "group": "Packaging",
        "label": "Site Bytes Warning",
        "kind": "integer",
        "default": 800 * 1024 * 1024,
        "help": "Warn when total site media reaches this many bytes. Empty uses the default.",
    },
    {
        "path": "packaging.warn_mp4_bytes",
        "group": "Packaging",
        "label": "MP4 Bytes Warning",
        "kind": "integer",
        "default": 150 * 1024 * 1024,
        "help": "Warn when one MP4 reaches this many bytes. Empty uses the default.",
    },
)


def entrypoint_to_string(entrypoint: SceneEntrypoint) -> str:
    """Return the current user-facing string convention for one entrypoint."""
    if entrypoint.renderer is None:
        return entrypoint.target
    return f"{entrypoint.target}@{entrypoint.renderer}"


def validate_entrypoint_string(value: str) -> SceneEntrypoint:
    """Validate one current-convention entrypoint string."""
    target, separator, renderer = value.rpartition("@")
    if not separator:
        return SceneEntrypoint(target=value)
    return SceneEntrypoint(target=target, renderer=cast(RendererName, renderer))


def available_quality_options() -> tuple[QualityOption, ...]:
    """Return Manim quality options from Manim's own constants."""
    from manim.constants import QUALITIES

    options: list[QualityOption] = []
    for name, data in QUALITIES.items():
        flag = data.get("flag")
        if not isinstance(flag, str) or not flag:
            continue
        pixel_width = int(data["pixel_width"])
        pixel_height = int(data["pixel_height"])
        frame_rate = int(data["frame_rate"])
        label = name.removesuffix("_quality").replace("_", " ").title()
        options.append(
            {
                "name": name,
                "label": label,
                "flag": flag,
                "pixel_width": pixel_width,
                "pixel_height": pixel_height,
                "frame_rate": frame_rate,
            }
        )
    return tuple(sorted(options, key=lambda option: option["pixel_height"]))


def manim_args_for_options(
    *,
    quality: str | None = None,
    cache: CacheMode = "on",
    preview: bool = False,
) -> tuple[str, ...]:
    """Build Manim passthrough args from manager controls."""
    args: list[str] = []
    if quality and quality != "default":
        options = available_quality_options()
        flags_by_name = {option["name"]: option["flag"] for option in options}
        flags_by_flag = {option["flag"]: option["flag"] for option in options}
        flag = flags_by_name.get(quality) or flags_by_flag.get(quality)
        if flag is None:
            known = ", ".join(option["name"] for option in options)
            raise ValueError(f"unknown quality {quality!r}; known: default, {known}")
        args.extend(("-q", flag))
    if cache == "off":
        args.append("--disable_caching")
    elif cache == "flush":
        args.append("--flush_cache")
    elif cache != "on":
        raise ValueError("cache must be 'on', 'off', or 'flush'")
    if preview:
        args.append("-p")
    return tuple(args)


def load_manager_state(repo_root: Path) -> dict[str, object]:
    """Return all data needed by the manager UI."""
    site_cfg = SiteConfig.load(repo_root=repo_root)
    registry = discover(repo_root / "decks", default_section_order=site_cfg.default_section_order)
    decks = [_deck_view(repo_root, deck, site_cfg) for deck in registry.all_decks]
    sections = [
        {
            "slug": section.config.slug,
            "title": section.config.title,
            "decks": [deck.slug for deck in section.decks],
        }
        for section in registry.sections
    ]
    return {
        "brand": site_cfg.brand,
        "repoRoot": str(repo_root),
        "sections": sections,
        "decks": decks,
        "deckOptions": _deck_option_specs_view(),
        "qualities": available_quality_options(),
        "slideThemes": ("all", "dark", "light"),
        "cacheModes": ("on", "off", "flush"),
    }


def update_deck_entrypoints(repo_root: Path, slug: str, entrypoints: tuple[str, ...]) -> None:
    """Atomically rewrite only the current-convention entrypoints list."""
    deck = _find_deck(repo_root, slug)
    parsed = tuple(validate_entrypoint_string(value) for value in entrypoints)
    targets = [entrypoint.target for entrypoint in parsed]
    duplicates = sorted({target for target in targets if targets.count(target) > 1})
    if duplicates:
        raise ValueError(f"duplicate entrypoint target(s): {duplicates!r}")

    toml_path = deck.path / "deck.toml"
    data = tomllib.loads(toml_path.read_text(encoding="utf-8"))
    data["entrypoints"] = list(entrypoints)
    DeckConfig(**data, path=deck.path, section_slug=deck.section_slug)

    text = tomli_w.dumps(data)
    tmp = toml_path.with_name(f".{toml_path.name}.tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(toml_path)


def update_deck_defaults(repo_root: Path, slug: str, values: dict[str, object]) -> None:
    """Atomically update deck-level TOML defaults from manager form values."""
    deck = _find_deck(repo_root, slug)
    known = {spec["path"] for spec in _DECK_OPTION_SPECS}
    unknown = sorted(set(values) - known)
    if unknown:
        raise ValueError(f"unknown deck option(s): {unknown!r}")

    toml_path = deck.path / "deck.toml"
    data = tomllib.loads(toml_path.read_text(encoding="utf-8"))
    for spec in _DECK_OPTION_SPECS:
        path = spec["path"]
        if spec.get("readonly") or path not in values:
            continue
        parsed = _parse_option_value(spec, values[path])
        if _should_remove_option(spec, parsed):
            _delete_nested(data, path)
        else:
            _set_nested(data, path, parsed)

    DeckConfig(**data, path=deck.path, section_slug=deck.section_slug)
    _prune_empty_tables(data)
    text = tomli_w.dumps(data)
    tmp = toml_path.with_name(f".{toml_path.name}.tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(toml_path)


def _find_deck(repo_root: Path, slug: str) -> DeckConfig:
    site_cfg = SiteConfig.load(repo_root=repo_root)
    registry = discover(repo_root / "decks", default_section_order=site_cfg.default_section_order)
    deck = registry.find_deck(slug)
    if deck is None:
        raise ValueError(f"unknown deck: {slug}")
    return deck


def _deck_view(repo_root: Path, deck: DeckConfig, site_cfg: SiteConfig) -> dict[str, object]:
    configured = tuple(entrypoint_to_string(entrypoint) for entrypoint in deck.scene_entrypoints)
    configured_targets = {entrypoint.target for entrypoint in deck.scene_entrypoints}
    entrypoints = [_entrypoint_view(repo_root, deck, value) for value in configured]
    available = [
        _entrypoint_view(repo_root, deck, value, configured=False)
        for value in _available_entrypoint_strings(deck)
        if validate_entrypoint_string(value).target not in configured_targets
    ]
    slide_themes = themes.resolve_slide_themes(deck, site_cfg.slide_themes)
    return {
        "slug": deck.slug,
        "title": deck.title,
        "summary": deck.summary,
        "section": deck.section_slug,
        "path": _rel(repo_root, deck.path),
        "entrypoints": entrypoints,
        "available": available,
        "rendered": _rendered_status(repo_root, deck),
        "defaults": _deck_defaults_view(deck),
        "slideThemes": {
            "enabled": slide_themes.enabled,
            "dark": slide_themes.dark,
            "light": slide_themes.light,
            "default": slide_themes.default,
        },
    }


def _entrypoint_view(
    repo_root: Path,
    deck: DeckConfig,
    value: str,
    *,
    configured: bool = True,
) -> dict[str, object]:
    try:
        entrypoint = validate_entrypoint_string(value)
        module, _, scene = entrypoint.target.partition(":")
        source = deck._module_to_file(module)
        source_renderer = detect_source_renderer(source)
        renderer = entrypoint.renderer or source_renderer or "cairo"
        conflict = (
            entrypoint.renderer is not None
            and source_renderer is not None
            and entrypoint.renderer != source_renderer
        )
        return {
            "value": value,
            "target": entrypoint.target,
            "module": module,
            "scene": scene,
            "configured": configured,
            "sourceFile": _rel(repo_root, source),
            "renderer": renderer,
            "explicitRenderer": entrypoint.renderer,
            "sourceRenderer": source_renderer,
            "error": "renderer conflict" if conflict else "",
        }
    except Exception as exc:
        return {
            "value": value,
            "target": value,
            "module": "",
            "scene": value.rsplit(":", 1)[-1].rsplit("@", 1)[0],
            "configured": configured,
            "sourceFile": "",
            "renderer": "unknown",
            "explicitRenderer": None,
            "sourceRenderer": None,
            "error": str(exc),
        }


def _deck_option_specs_view() -> list[dict[str, object]]:
    return [dict(spec) for spec in _DECK_OPTION_SPECS]


def _deck_defaults_view(deck: DeckConfig) -> dict[str, DeckOptionValue]:
    toml_path = deck.path / "deck.toml"
    raw = tomllib.loads(toml_path.read_text(encoding="utf-8"))
    values: dict[str, DeckOptionValue] = {}
    dumped = deck.model_dump(mode="json")
    for spec in _DECK_OPTION_SPECS:
        path = spec["path"]
        raw_value = _get_nested(raw, path)
        present = raw_value is not _UNSET
        value = raw_value if present else _get_nested(dumped, path)
        if value is _UNSET:
            value = ""
        values[path] = {"value": _ui_value(value), "present": present}
    return values


def _parse_option_value(spec: DeckOptionSpec, value: object) -> object:
    kind = spec["kind"]
    if kind == "boolean":
        if value in ("", None, "default"):
            return None
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"true", "1", "yes", "on"}:
                return True
            if normalized in {"false", "0", "no", "off"}:
                return False
        raise ValueError(f"{spec['label']} must be on, off, or default")
    if kind == "integer":
        if value in ("", None):
            return None
        if isinstance(value, int) and not isinstance(value, bool):
            return value
        if isinstance(value, str):
            return int(value.strip())
        raise ValueError(f"{spec['label']} must be an integer")
    if kind == "date":
        if value in ("", None):
            return None
        if isinstance(value, dt.date):
            return value
        if isinstance(value, str):
            text = value.strip()
            return dt.date.fromisoformat(text) if text else None
        raise ValueError(f"{spec['label']} must be a YYYY-MM-DD date")
    if kind == "integer_list":
        return tuple(int(item) for item in _split_list(value))
    if kind == "string_list":
        return tuple(_split_list(value))
    if kind == "select":
        if value in ("", None, "default"):
            return None
        text = str(value).strip()
        choices = spec.get("choices", ())
        if text not in choices:
            raise ValueError(f"{spec['label']} must be one of: {', '.join(choices)}")
        return text
    if value in (None,):
        return ""
    return str(value).strip()


def _split_list(value: object) -> tuple[str, ...]:
    if value in ("", None):
        return ()
    if isinstance(value, list | tuple):
        return tuple(str(item).strip() for item in value if str(item).strip())
    text = str(value)
    parts: list[str] = []
    for line in text.replace(",", "\n").splitlines():
        item = line.strip()
        if item:
            parts.append(item)
    return tuple(parts)


def _should_remove_option(spec: DeckOptionSpec, value: object) -> bool:
    if spec.get("required"):
        return False
    if value in (None, "", (), []):
        return True
    default = spec.get("default", _UNSET)
    if default is _UNSET:
        return False
    normalized = tuple(value) if isinstance(value, list) else value
    return normalized == default


def _get_nested(data: dict[str, object], path: str) -> object:
    cursor: object = data
    for part in path.split("."):
        if not isinstance(cursor, dict) or part not in cursor:
            return _UNSET
        cursor = cursor[part]
    return cursor


def _set_nested(data: dict[str, object], path: str, value: object) -> None:
    parts = path.split(".")
    cursor = data
    for part in parts[:-1]:
        next_value = cursor.get(part)
        if not isinstance(next_value, dict):
            next_value = {}
            cursor[part] = next_value
        cursor = cast(dict[str, object], next_value)
    value_to_write: object = list(value) if isinstance(value, tuple) else value
    cursor[parts[-1]] = value_to_write


def _delete_nested(data: dict[str, object], path: str) -> None:
    parts = path.split(".")
    cursor = data
    parents: list[tuple[dict[str, object], str]] = []
    for part in parts[:-1]:
        next_value = cursor.get(part)
        if not isinstance(next_value, dict):
            return
        parents.append((cursor, part))
        cursor = cast(dict[str, object], next_value)
    cursor.pop(parts[-1], None)
    for parent, part in reversed(parents):
        value = parent.get(part)
        if isinstance(value, dict) and not value:
            parent.pop(part, None)


def _prune_empty_tables(data: dict[str, object]) -> None:
    for key in tuple(data):
        value = data[key]
        if isinstance(value, dict):
            _prune_empty_tables(cast(dict[str, object], value))
            if not value:
                data.pop(key, None)


def _ui_value(value: object) -> object:
    if isinstance(value, dt.date):
        return value.isoformat()
    if isinstance(value, Path):
        return value.as_posix()
    if isinstance(value, tuple):
        return [_ui_value(item) for item in value]
    if isinstance(value, list):
        return [_ui_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _ui_value(item) for key, item in value.items()}
    return value


def _available_entrypoint_strings(deck: DeckConfig) -> tuple[str, ...]:
    entries: list[str] = []
    roots = [deck.path / "slides", deck.path / "slides.py"]
    for root in roots:
        files: tuple[Path, ...]
        if root.is_file():
            files = (root,)
        elif root.is_dir():
            files = tuple(
                path for path in sorted(root.rglob("*.py")) if "__pycache__" not in path.parts
            )
        else:
            files = ()
        for source in files:
            module = _module_for_source(deck.path, source)
            if not module:
                continue
            source_renderer = detect_source_renderer(source)
            for class_name in _scene_classes(source):
                target = f"{module}:{class_name}"
                entries.append(f"{target}@opengl" if source_renderer == "opengl" else target)
    return tuple(dict.fromkeys(entries))


def _module_for_source(deck_path: Path, source: Path) -> str:
    rel = source.relative_to(deck_path)
    parts = rel.parent.parts if rel.name == "__init__.py" else rel.with_suffix("").parts
    return ".".join(parts)


def _scene_classes(source: Path) -> tuple[str, ...]:
    try:
        tree = ast.parse(source.read_text(encoding="utf-8"), filename=str(source))
    except (OSError, SyntaxError, UnicodeDecodeError):
        return ()
    names: list[str] = []
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and _looks_like_scene_class(node):
            names.append(node.name)
    return tuple(names)


def _looks_like_scene_class(node: ast.ClassDef) -> bool:
    if not node.bases:
        return False
    for base in node.bases:
        name = _base_name(base)
        if name in _SCENE_BASE_NAMES or name.endswith("Scene") or name.endswith("Slide"):
            return True
    return False


def _base_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Subscript):
        return _base_name(node.value)
    return ""


def _rendered_status(repo_root: Path, deck: DeckConfig) -> dict[str, object]:
    manifest = repo_root / "site" / "decks" / deck.slug / "simplex-manifest.json"
    if not manifest.exists():
        return {"manifest": "", "slideCount": 0, "duration": 0.0, "themes": []}
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {
            "manifest": _rel(repo_root, manifest),
            "slideCount": 0,
            "duration": 0.0,
            "themes": [],
        }
    cues = data.get("cues")
    themes_raw = data.get("themes")
    themes_view = []
    if isinstance(themes_raw, list):
        for theme in themes_raw:
            if isinstance(theme, dict):
                themes_view.append(
                    {
                        "id": str(theme.get("id", "")),
                        "strategy": str(theme.get("strategy", "")),
                        "hasMp4": bool((theme.get("media") or {}).get("mp4"))
                        if isinstance(theme.get("media"), dict)
                        else False,
                    }
                )
    return {
        "manifest": _rel(repo_root, manifest),
        "slideCount": len(cues) if isinstance(cues, list) else 0,
        "duration": float(data.get("duration") or 0.0) if isinstance(data, dict) else 0.0,
        "themes": themes_view,
    }


def _rel(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def scene_renderer(repo_root: Path, slug: str, scene: str) -> RendererName:
    """Resolve the renderer used for one scene class in a deck."""
    deck = _find_deck(repo_root, slug)
    for group in deck.resolve_entrypoints():
        if scene in group.scene_names:
            return group.renderer
    raise ValueError(f"unknown scene {scene!r} in deck {slug!r}")
