"""Build the Simplex static portal and timeline-native deck pages."""

from __future__ import annotations

import contextlib
import datetime as dt
import hashlib
import html as html_lib
import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from jinja2 import Environment, PackageLoader, select_autoescape

from simplex.deck.config import (
    DeckConfig,
    PackagingConfig,
    ResolvedSlideThemes,
    SlideThemeSelection,
    SlideThemeVariant,
)
from simplex.deck.registry import Section, SectionedRegistry, discover
from simplex.deck.section import SectionConfig
from simplex.manifest import (
    DeckManifest,
    ManifestCompat,
    ManifestExports,
    ThemeMedia,
    ThemeTimeline,
)
from simplex.render import filenames, notes_pdf, pdf, runner, themes, thumbnail, timeline
from simplex.render.timeline import PackagedTheme, RenderedUnit
from simplex.theme.presets import get as get_theme
from simplex.theme.web_css import render_web_css
from simplex.web import notes, vendor
from simplex.web.bibliography import Bibliography
from simplex.web.site_config import SiteConfig


@dataclass(frozen=True, slots=True)
class _SlideView:
    index: int
    cue_id: str
    scene: str
    name: str
    duration_s: float
    thumbnail: str | None
    theme_thumbnails: dict[str, str]


@dataclass(frozen=True, slots=True)
class _DeckCardAssets:
    thumbnail: str | None
    theme_thumbnails: dict[str, str]
    preview_gif: str | None
    theme_preview_gifs: dict[str, str]


@dataclass(frozen=True, slots=True)
class _DeckDateInfo:
    value: dt.date
    timestamp: float
    label: str
    iso: str
    source: str


def _static_source_dir() -> Path:
    return Path(__file__).parent / "static"


def _file_version(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return ""
    digest = hashlib.blake2s(digest_size=6)
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _with_version(url: str, version: str) -> str:
    if not version:
        return url
    separator = "&" if "?" in url else "?"
    return f"{url}{separator}v={version}"


def _jinja(site_cfg: SiteConfig) -> Environment:
    env = Environment(
        loader=PackageLoader("simplex.web", "templates"),
        autoescape=select_autoescape(["html", "j2"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )

    def static(path: str) -> str:
        clean = path.lstrip("/")
        url = site_cfg.url("static/" + clean)
        return _with_version(url, _file_version(_static_source_dir() / clean))

    globals_: dict[str, Any] = cast(dict[str, Any], env.globals)
    globals_["static"] = static
    globals_["site"] = site_cfg
    return env


def _copy_static(site_dir: Path) -> None:
    src = _static_source_dir()
    src.mkdir(parents=True, exist_ok=True)
    vendor.ensure(src)
    dst = site_dir / "static"
    dst.mkdir(parents=True, exist_ok=True)
    for entry in src.iterdir():
        if entry.name in {"README.md", ".gitkeep", "tailwind.input.css"}:
            continue
        target = dst / entry.name
        if entry.is_dir():
            shutil.copytree(entry, target, dirs_exist_ok=True)
        else:
            shutil.copy2(entry, target)


def _theme_label(variant: str) -> str:
    return variant[:1].upper() + variant[1:]


def _cache_dir(site_dir: Path, deck: DeckConfig, variant: str) -> Path:
    return site_dir.parent / ".simplex_cache" / "decks" / deck.slug / variant


def _render_variant(
    deck: DeckConfig,
    *,
    variant: SlideThemeVariant,
    site_dir: Path,
    render: bool,
    manim_args: tuple[str, ...],
    scenes: tuple[str, ...],
    write_last_frame: bool = False,
) -> tuple[Path, tuple[RenderedUnit, ...]]:
    media_dir = _cache_dir(site_dir, deck, variant) / "intermediate"
    if render:
        if scenes:
            unknown = tuple(scene for scene in scenes if scene not in deck.scene_class_names)
            if unknown:
                raise ValueError(f"unknown scene name(s): {list(unknown)!r}")
            deck_scenes = tuple(scene for scene in scenes if scene in deck.scene_class_names)
            render_scenes = deck_scenes
        else:
            deck_scenes = deck.scene_class_names
            render_scenes = _changed_render_scenes(
                deck,
                variant=variant,
                media_dir=media_dir,
                manim_args=manim_args,
                candidates=deck_scenes,
            )
        if render_scenes:
            runner.render(
                deck,
                output_dir=media_dir,
                manim_args=manim_args,
                scenes=render_scenes,
                write_last_frame=write_last_frame,
            )
            if not scenes:
                _write_render_state(
                    deck,
                    variant=variant,
                    media_dir=media_dir,
                    manim_args=manim_args,
                    scenes=deck_scenes,
                )
    return media_dir, timeline.load_units(deck, media_dir=media_dir)


def _changed_render_scenes(
    deck: DeckConfig,
    *,
    variant: SlideThemeVariant,
    media_dir: Path,
    manim_args: tuple[str, ...],
    candidates: tuple[str, ...],
) -> tuple[str, ...]:
    state = _load_render_state(media_dir)
    fingerprints = _scene_fingerprints(deck, variant=variant, manim_args=manim_args)
    existing = {unit.scene: unit for unit in timeline.load_units(deck, media_dir=media_dir)}
    changed: list[str] = []
    for scene in candidates:
        unit = existing.get(scene)
        if state.get(scene) != fingerprints.get(scene) or not _unit_is_reusable(unit):
            changed.append(scene)
    return tuple(changed)


def _unit_is_reusable(unit: RenderedUnit | None) -> bool:
    return bool(unit and unit.video is not None and unit.video.exists() and unit.cues)


def _render_state_path(media_dir: Path) -> Path:
    return media_dir.parent / "render-state.json"


def _load_render_state(media_dir: Path) -> dict[str, str]:
    path = _render_state_path(media_dir)
    if not path.exists():
        return {}
    with contextlib.suppress(OSError, json.JSONDecodeError):
        raw = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(raw, dict):
            return {str(key): str(value) for key, value in raw.items()}
    return {}


def _write_render_state(
    deck: DeckConfig,
    *,
    variant: SlideThemeVariant,
    media_dir: Path,
    manim_args: tuple[str, ...],
    scenes: tuple[str, ...],
) -> None:
    fingerprints = _scene_fingerprints(deck, variant=variant, manim_args=manim_args)
    state = _load_render_state(media_dir)
    for scene in scenes:
        if scene in fingerprints:
            state[scene] = fingerprints[scene]
    path = _render_state_path(media_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")


def _scene_fingerprints(
    deck: DeckConfig,
    *,
    variant: SlideThemeVariant,
    manim_args: tuple[str, ...],
) -> dict[str, str]:
    source_files = {
        class_name: group.source_file
        for group in deck.resolve_entrypoints()
        for class_name in group.scene_names
    }
    config_files = tuple(path for path in _fingerprint_config_paths(deck) if path.exists())
    out: dict[str, str] = {}
    for scene in deck.scene_class_names:
        digest = hashlib.blake2s(digest_size=16)
        digest.update(b"simplex-render-v3\0")
        digest.update(variant.encode())
        digest.update(b"\0")
        digest.update((deck.slide_theme_variant or "").encode())
        digest.update(b"\0")
        digest.update("\0".join(manim_args).encode())
        digest.update(b"\0")
        for path in (
            *_simplex_runtime_fingerprint_paths(),
            *config_files,
            deck.path / "deck.toml",
            source_files[scene],
        ):
            digest.update(path.resolve().as_posix().encode())
            digest.update(b"\0")
            with contextlib.suppress(OSError):
                digest.update(path.read_bytes())
            digest.update(b"\0")
        out[scene] = digest.hexdigest()
    return out


def _simplex_runtime_fingerprint_paths() -> tuple[Path, ...]:
    root = Path(__file__).resolve().parents[1]
    return tuple(sorted(root.rglob("*.py")))


def _fingerprint_config_paths(deck: DeckConfig) -> tuple[Path, ...]:
    return (
        deck.path / "manim.cfg",
        deck.path.parent / "manim.cfg",
        deck.path.parent.parent / "manim.cfg",
    )


def _package_existing_or_rendered(
    *,
    deck: DeckConfig,
    variant: SlideThemeVariant,
    background: str,
    units: tuple[RenderedUnit, ...],
    cues: tuple[Any, ...],
    deck_out: Path,
    media_base_url: str,
    segment_duration: int,
) -> PackagedTheme:
    media_dir = deck_out / "media" / variant
    media_href = f"media/{variant}"
    existing_lecture = media_dir / "lecture.mp4"
    existing_hls = media_dir / "hls" / "master.m3u8"
    if (
        not any(unit.video is not None and unit.video.exists() for unit in units)
        and existing_lecture.exists()
    ):
        theme_media = {
            "hls": f"{media_href}/hls/master.m3u8" if existing_hls.exists() else None,
            "mp4": f"{media_href}/lecture.mp4",
        }
        theme = ThemeTimeline(
            id=variant,
            label=_theme_label(variant),
            strategy="rendered",
            media=ThemeMedia(**theme_media),
            duration=timeline.media_duration(existing_lecture),
            background=background,
        )
        if media_base_url:
            theme = timeline.prefix_media_urls(theme, media_base_url)
        return PackagedTheme(
            theme=theme,
            progressive_mode="copy",
            hls_available=existing_hls.exists(),
            warnings=(),
            lecture_mp4=existing_lecture,
        )
    packaged = timeline.package_theme(
        theme_id=variant,
        label=_theme_label(variant),
        background=background,
        units=units,
        cues=tuple(cues),
        output_dir=media_dir,
        media_href_prefix=media_href,
        segment_duration=segment_duration,
    )
    if media_base_url:
        packaged = PackagedTheme(
            theme=timeline.prefix_media_urls(packaged.theme, media_base_url),
            progressive_mode=packaged.progressive_mode,
            hls_available=packaged.hls_available,
            warnings=packaged.warnings,
            lecture_mp4=packaged.lecture_mp4,
        )
    return packaged


def _missing_theme_fallback(
    *,
    variant: SlideThemeVariant,
    background: str,
    source: PackagedTheme,
    media_base_url: str,
) -> PackagedTheme:
    fallback = timeline.css_filter_fallback_theme(
        theme_id=variant,
        label=_theme_label(variant),
        source=source.theme,
        background=background,
    )
    if media_base_url:
        fallback = timeline.prefix_media_urls(fallback, media_base_url)
    return PackagedTheme(
        theme=fallback,
        progressive_mode=source.progressive_mode,
        hls_available=source.hls_available,
        warnings=(f"theme {variant!r} is using CSS-filter fallback media",),
        lecture_mp4=source.lecture_mp4,
    )


def _cue_slides(
    manifest: DeckManifest,
    *,
    theme_posters: dict[str, dict[str, str]],
) -> tuple[_SlideView, ...]:
    slides: list[_SlideView] = []
    for cue in manifest.cues:
        if not cue.kind.is_slide:
            continue
        per_theme = {
            variant: posters[cue.id]
            for variant, posters in theme_posters.items()
            if cue.id in posters
        }
        slides.append(
            _SlideView(
                index=cue.ordinal,
                cue_id=cue.id,
                scene=cue.unit,
                name=cue.title,
                duration_s=cue.duration,
                thumbnail=cue.thumbnail,
                theme_thumbnails=per_theme,
            )
        )
    if slides:
        return tuple(slides)
    return tuple(
        _SlideView(
            index=cue.ordinal,
            cue_id=cue.id,
            scene=cue.unit,
            name=cue.title,
            duration_s=cue.duration,
            thumbnail=cue.thumbnail,
            theme_thumbnails={
                variant: posters[cue.id]
                for variant, posters in theme_posters.items()
                if cue.id in posters
            },
        )
        for cue in manifest.cues
    )


def _slide_ref_labels(slides: tuple[_SlideView, ...]) -> dict[str, tuple[int, str]]:
    from simplex.web.slide_ref import label_key

    refs: dict[str, tuple[int, str]] = {}
    for slide in slides:
        candidates = {
            str(slide.index),
            slide.cue_id,
            slide.name,
            label_key(slide.name),
            slide.scene,
            label_key(slide.scene),
        }
        for candidate in candidates:
            key = label_key(candidate)
            if key:
                refs.setdefault(key, (slide.index, slide.name))
    return refs


def _load_bibliography(deck_path: Path) -> Bibliography | None:
    refs = deck_path / "refs.bib"
    return Bibliography.load(refs) if refs.exists() else None


def _with_notes_date(notes_html: str, info: _DeckDateInfo | None) -> str:
    if info is None:
        return notes_html
    date_html = (
        '<p class="deck-notes-date">'
        f'<time datetime="{html_lib.escape(info.iso)}">{html_lib.escape(info.label)}</time>'
        "</p>"
    )
    lower = notes_html.lower()
    h1_end = lower.find("</h1>")
    if h1_end == -1:
        return f"{date_html}\n{notes_html}"
    insert_at = h1_end + len("</h1>")
    return f"{notes_html[:insert_at]}\n{date_html}{notes_html[insert_at:]}"


def _build_notes(
    deck: DeckConfig,
    *,
    deck_out: Path,
    slides: tuple[_SlideView, ...],
    render: bool,
    deck_date_info: _DeckDateInfo | None,
) -> str:
    notes_md = deck.path / "notes.md"
    if not notes_md.exists():
        return ""
    slide_refs = _slide_ref_labels(slides)
    bib = _load_bibliography(deck.path)
    notes_html = notes.render(
        notes_md,
        slide_count=len(slides),
        slide_refs=slide_refs,
        bibliography=bib,
        code_style=deck.resolved_notes_code_style(),
    )
    if deck.web.show_notes_date:
        notes_html = _with_notes_date(notes_html, deck_date_info)
    if render:
        with contextlib.suppress(subprocess.SubprocessError, FileNotFoundError, ImportError):
            notes_pdf.export(
                deck,
                notes_md,
                output_dir=deck_out,
                slide_refs=slide_refs,
                bibliography=bib,
                note_date=deck_date_info.value
                if deck.web.show_notes_date and deck_date_info is not None
                else None,
            )
    return notes_html


def _has_notes_pdf(deck: DeckConfig, deck_dir: Path) -> bool:
    return (deck_dir / filenames.pdf_name(deck, "note")).exists()


def _export_slide_pdfs(
    deck: DeckConfig,
    manifest: DeckManifest,
    *,
    deck_out: Path,
    default_variant: SlideThemeVariant,
    theme_posters: dict[str, dict[str, str]],
) -> dict[str, str]:
    export_dir = deck_out / "exports"
    legacy_pdf = export_dir / filenames.pdf_name(deck, "slides")
    with contextlib.suppress(FileNotFoundError):
        legacy_pdf.unlink()

    hrefs: dict[str, str] = {}
    for theme in manifest.themes:
        slides_pdf = pdf.export(
            deck,
            manifest,
            output_dir=deck_out,
            variant=theme.id,
            posters=theme_posters.get(theme.id, {}),
            css_filter=theme.css_filter if theme.strategy == "css_filter_fallback" else None,
        )
        hrefs[theme.id] = slides_pdf.relative_to(deck_out).as_posix()

    default_pdf = hrefs.get(default_variant) or next(iter(hrefs.values()), "")
    return {"default": default_pdf, **hrefs} if default_pdf else hrefs


def _deck_media_base_url(deck: DeckConfig, site_cfg: SiteConfig) -> str:
    return deck.hosting.media_base_url or site_cfg.hosting.media_base_url


def _budget_warnings(deck_out: Path, deck: DeckConfig, site_cfg: SiteConfig) -> tuple[str, ...]:
    packaging = _effective_packaging(deck, site_cfg)
    warnings: list[str] = []
    total_bytes = sum(path.stat().st_size for path in deck_out.rglob("*") if path.is_file())
    if total_bytes >= packaging.warn_site_bytes:
        warnings.append(f"deck output is {total_bytes / (1024 * 1024):.1f} MiB")
    for mp4 in (deck_out / "media").glob("*/lecture.mp4"):
        size = mp4.stat().st_size
        if size >= packaging.warn_mp4_bytes:
            warnings.append(
                f"{mp4.relative_to(deck_out).as_posix()} is {size / (1024 * 1024):.1f} MiB"
            )
    return tuple(warnings)


def _packaging_segment_duration(deck: DeckConfig, site_cfg: SiteConfig) -> int:
    return _effective_packaging(deck, site_cfg).hls_segment_duration


def _effective_packaging(deck: DeckConfig, site_cfg: SiteConfig) -> PackagingConfig:
    default = PackagingConfig()
    return site_cfg.packaging if deck.packaging == default else deck.packaging


def _slide_background_for_variant(
    slide_theme_config: ResolvedSlideThemes,
    variant: SlideThemeVariant,
) -> str:
    theme = get_theme(slide_theme_config.theme_name(variant), variant=variant)
    return theme.palette.background


def _build_deck(
    deck: DeckConfig,
    *,
    site_dir: Path,
    site_cfg: SiteConfig,
    env: Environment,
    render: bool,
    deck_date_info: _DeckDateInfo | None,
    manim_args: tuple[str, ...],
    scenes: tuple[str, ...],
    theme_selection: SlideThemeSelection,
    watch: bool,
) -> _DeckCardAssets:
    del watch
    deck_out = site_dir / "decks" / deck.slug
    deck_out.mkdir(parents=True, exist_ok=True)
    media_base_url = _deck_media_base_url(deck, site_cfg)
    slide_theme_config = themes.resolve_slide_themes(deck, site_cfg.slide_themes)
    requested_variants = (
        themes.selected_variants(slide_theme_config, theme_selection)
        if slide_theme_config.enabled
        else ("dark",)
    )
    default_variant = (
        slide_theme_config.default_variant(requested_variants)
        if slide_theme_config.enabled
        else "dark"
    )
    slide_backgrounds: dict[SlideThemeVariant, str] = {
        "dark": _slide_background_for_variant(slide_theme_config, "dark"),
        "light": _slide_background_for_variant(slide_theme_config, "light"),
    }

    units_by_variant: dict[SlideThemeVariant, tuple[RenderedUnit, ...]] = {}
    packaged_by_variant: dict[SlideThemeVariant, PackagedTheme] = {}
    for variant in requested_variants:
        themed_deck = (
            themes.variant_deck(deck, slide_theme_config, variant)
            if slide_theme_config.enabled
            else deck.model_copy(update={"slide_theme_variant": "dark"})
        )
        _media_dir, units = _render_variant(
            themed_deck,
            variant=variant,
            site_dir=site_dir,
            render=render,
            manim_args=manim_args,
            scenes=scenes,
        )
        if not render:
            units = _hydrate_units_from_existing_media(
                units,
                deck_out / "media" / variant / "lecture.mp4",
            )
        units_by_variant[variant] = units

    default_units = units_by_variant[default_variant]
    fps = default_units[0].fps if default_units else timeline.DEFAULT_FPS
    cues = timeline.rebase_cues(default_units, fps=fps)
    warnings: list[str] = []
    for variant, units in units_by_variant.items():
        if variant != default_variant:
            warnings.extend(timeline.validate_theme_cues(default_units, units, theme_id=variant))
        packaged_by_variant[variant] = _package_existing_or_rendered(
            deck=deck,
            variant=variant,
            background=slide_backgrounds[variant],
            units=units,
            cues=cues,
            deck_out=deck_out,
            media_base_url=media_base_url,
            segment_duration=_packaging_segment_duration(deck, site_cfg),
        )
        warnings.extend(packaged_by_variant[variant].warnings)

    # Always expose dark/light controls. Missing requested renders degrade to a
    # CSS-filter fallback that maps onto the default rendered media.
    if slide_theme_config.enabled:
        for variant in ("dark", "light"):
            if variant not in packaged_by_variant:
                packaged_by_variant[variant] = _missing_theme_fallback(
                    variant=variant,
                    background=slide_backgrounds[variant],
                    source=packaged_by_variant[default_variant],
                    media_base_url=media_base_url,
                )
                warnings.extend(packaged_by_variant[variant].warnings)
    else:
        packaged_by_variant["light"] = _missing_theme_fallback(
            variant="light",
            background=slide_backgrounds["light"],
            source=packaged_by_variant["dark"],
            media_base_url=media_base_url,
        )
        warnings.extend(packaged_by_variant["light"].warnings)

    theme_posters: dict[str, dict[str, str]] = {}
    default_images = None
    for variant, packaged in packaged_by_variant.items():
        images = thumbnail.generate_cue_images(
            deck,
            cues,
            theme_id=variant,
            lecture_mp4=packaged.lecture_mp4,
            site_deck_dir=deck_out,
            cache_dir=deck_out,
            thumbnails=(variant == default_variant),
        )
        theme_posters[variant] = {
            cue_id: path.as_posix() for cue_id, path in images.posters.items()
        }
        if variant == default_variant:
            default_images = images

    if default_images is not None:
        cues = tuple(
            cue.model_copy(
                update={
                    "thumbnail": _asset_str(default_images.thumbnails.get(cue.id, cue.thumbnail)),
                    "poster": _asset_str(default_images.posters.get(cue.id, cue.poster)),
                }
            )
            for cue in cues
        )

    compat = ManifestCompat(
        progressive_mode=packaged_by_variant[default_variant].progressive_mode,
        player="shaka",
        hls=packaged_by_variant[default_variant].hls_available,
    )
    manifest = timeline.build_manifest(
        deck,
        cues=cues,
        themes=tuple(packaged.theme for packaged in packaged_by_variant.values()),
        warnings=tuple(warnings),
        compat=compat,
        media_base_url=media_base_url or ".",
        fps=fps,
    )
    slides = _cue_slides(manifest, theme_posters=theme_posters)

    notes_html = _build_notes(
        deck,
        deck_out=deck_out,
        slides=slides,
        render=render,
        deck_date_info=deck_date_info,
    )

    slide_pdf_hrefs = _export_slide_pdfs(
        deck,
        manifest,
        deck_out=deck_out,
        default_variant=default_variant,
        theme_posters=theme_posters,
    )
    manifest = manifest.model_copy(
        update={
            "exports": ManifestExports(
                pdf=slide_pdf_hrefs.get("default"),
                notes_pdf=filenames.pdf_name(deck, "note")
                if _has_notes_pdf(deck, deck_out)
                else None,
            ),
            "budget_warnings": (
                *manifest.budget_warnings,
                *_budget_warnings(deck_out, deck, site_cfg),
            ),
        }
    )
    (deck_out / "simplex-manifest.json").write_text(manifest.to_public_json(), encoding="utf-8")

    preview_gif = thumbnail.generate_carousel_gif(
        deck,
        manifest.cues,
        lecture_mp4=packaged_by_variant[default_variant].lecture_mp4,
        site_deck_dir=deck_out,
        cache_dir=deck_out,
    )
    initial_player_frames = {
        variant: posters[manifest.cues[0].id]
        for variant, posters in theme_posters.items()
        if manifest.cues and manifest.cues[0].id in posters
    }
    manifest_slide_backgrounds = {
        theme.id: theme.background for theme in manifest.themes if theme.background
    }
    default_slide_background = manifest_slide_backgrounds.get(default_variant) or next(
        iter(manifest_slide_backgrounds.values()),
        "",
    )
    slide_theme_mode = (
        "filter"
        if any(theme.strategy == "css_filter_fallback" for theme in manifest.themes)
        else "true"
    )
    page_theme_name = (
        slide_theme_config.theme_name(default_variant) if slide_theme_config.enabled else deck.theme
    )
    page = env.get_template("deck.html").render(
        deck=deck,
        slides=slides,
        slide_count=len(slides),
        total_duration_min=int(manifest.duration // 60)
        if manifest.duration > 0
        else deck.duration_minutes,
        has_pdf=bool(slide_pdf_hrefs),
        has_notes_pdf=_has_notes_pdf(deck, deck_out),
        slides_pdf_href=manifest.exports.pdf or "",
        slides_pdf_hrefs=slide_pdf_hrefs,
        notes_pdf_name=filenames.pdf_name(deck, "note"),
        notes_html=notes_html,
        palette_css=render_web_css(
            deck.resolved_web_palette(page_theme_name, variant=default_variant),
            code_style=deck.resolved_notes_code_style(),
        ),
        slide_theme_mode=slide_theme_mode,
        available_slide_themes=tuple(packaged_by_variant),
        default_slide_theme=default_variant,
        default_player_mode="presentation",
        player_manifest=manifest.model_dump(mode="json", exclude_none=True),
        initial_player_frames=initial_player_frames,
        slide_backgrounds=manifest_slide_backgrounds,
        default_slide_background=default_slide_background,
    )
    (deck_out / "index.html").write_text(page, encoding="utf-8")
    first_slide = slides[0] if slides else None
    first_cue_id = manifest.cues[0].id if manifest.cues else ""
    card_theme_thumbs = {
        variant: posters[first_cue_id]
        for variant, posters in theme_posters.items()
        if first_cue_id in posters
    }
    return _DeckCardAssets(
        thumbnail=first_slide.thumbnail if first_slide else None,
        theme_thumbnails=card_theme_thumbs,
        preview_gif=preview_gif.as_posix() if preview_gif is not None else None,
        theme_preview_gifs={},
    )


def _hydrate_units_from_existing_media(
    units: tuple[RenderedUnit, ...],
    lecture_mp4: Path,
) -> tuple[RenderedUnit, ...]:
    if not units or any(unit.video is not None for unit in units):
        return units
    duration = timeline.media_duration(lecture_mp4)
    if duration <= 0:
        return units
    fps = units[0].fps
    per_unit = duration / len(units)
    out: list[RenderedUnit] = []
    for unit in units:
        cue_count = max(1, len(unit.cues))
        per_cue = per_unit / cue_count
        cues = []
        for index, cue in enumerate(unit.cues):
            start = index * per_cue
            end = (index + 1) * per_cue
            cues.append(
                cue.model_copy(
                    update={
                        "start": start,
                        "end": end,
                        "start_frame": round(start * fps),
                        "end_frame": round(end * fps),
                    }
                )
            )
        out.append(
            RenderedUnit(
                scene=unit.scene,
                unit=unit.unit,
                source_file=unit.source_file,
                video=unit.video,
                fps=fps,
                duration=per_unit,
                duration_frames=round(per_unit * fps),
                cues=tuple(cues),
            )
        )
    return tuple(out)


def _build_section_page(
    section: Section,
    site_dir: Path,
    env: Environment,
    thumbs: dict[str, str | None],
    theme_thumbs: dict[str, dict[str, str]],
    preview_gifs: dict[str, str | None],
    theme_preview_gifs: dict[str, dict[str, str]],
    deck_dates: dict[str, str],
    palette_css: str,
) -> None:
    out = site_dir / "sections" / section.config.slug
    out.mkdir(parents=True, exist_ok=True)
    page = env.get_template("section.html").render(
        section=section,
        thumbs=thumbs,
        theme_thumbs=theme_thumbs,
        preview_gifs=preview_gifs,
        theme_preview_gifs=theme_preview_gifs,
        deck_dates=deck_dates,
        palette_css=palette_css,
    )
    (out / "index.html").write_text(page, encoding="utf-8")


def _build_index(
    registry: SectionedRegistry,
    site_dir: Path,
    env: Environment,
    thumbs: dict[str, str | None],
    theme_thumbs: dict[str, dict[str, str]],
    preview_gifs: dict[str, str | None],
    theme_preview_gifs: dict[str, dict[str, str]],
    deck_date_infos: dict[str, _DeckDateInfo | None],
    deck_dates: dict[str, str],
    palette_css: str,
) -> None:
    page = env.get_template("index.html").render(
        registry=registry,
        latest_section=_latest_section(registry, deck_date_infos),
        thumbs=thumbs,
        theme_thumbs=theme_thumbs,
        preview_gifs=preview_gifs,
        theme_preview_gifs=theme_preview_gifs,
        deck_dates=deck_dates,
        palette_css=palette_css,
    )
    (site_dir / "index.html").write_text(page, encoding="utf-8")


def _asset_str(value: object) -> str | None:
    if value is None:
        return None
    if isinstance(value, Path):
        return value.as_posix()
    return str(value)


def _site_palette_css(site_cfg: SiteConfig) -> str:
    from simplex.theme.presets import get as get_theme

    theme_name = getattr(site_cfg, "theme", None) or "simplex_dark"
    theme = get_theme(theme_name)
    return render_web_css(theme.web_palette, code_style=getattr(theme, "code_style", None))


def build(
    decks_dir: Path,
    site_dir: Path,
    *,
    render: bool = True,
    site_cfg: SiteConfig | None = None,
    only: tuple[str, ...] = (),
    manim_args: tuple[str, ...] = (),
    scenes: tuple[str, ...] = (),
    theme_selection: SlideThemeSelection = "all",
    watch: bool = False,
) -> None:
    """Discover decks, render/package timelines, and write static HTML."""
    site_cfg = site_cfg or SiteConfig.load(repo_root=decks_dir.parent)
    registry = discover(decks_dir, default_section_order=site_cfg.default_section_order)
    site_dir.mkdir(parents=True, exist_ok=True)
    env = _jinja(site_cfg)
    _copy_static(site_dir)

    only_set = set(only)
    deck_thumbs: dict[str, str | None] = {}
    deck_theme_thumbs: dict[str, dict[str, str]] = {}
    deck_preview_gifs: dict[str, str | None] = {}
    deck_theme_preview_gifs: dict[str, dict[str, str]] = {}
    deck_date_infos = {deck.slug: _deck_date_info(deck) for deck in registry.all_decks}
    deck_dates = {
        slug: info.label
        for slug, info in deck_date_infos.items()
        if info is not None and info.label
    }

    for section in registry.sections:
        for deck in section.decks:
            if only_set and deck.slug not in only_set:
                continue
            assets = _build_deck(
                deck,
                site_dir=site_dir,
                site_cfg=site_cfg,
                env=env,
                render=render,
                deck_date_info=deck_date_infos.get(deck.slug),
                manim_args=manim_args,
                scenes=scenes,
                theme_selection=theme_selection,
                watch=watch,
            )
            deck_thumbs[deck.slug] = assets.thumbnail
            deck_theme_thumbs[deck.slug] = assets.theme_thumbnails
            deck_preview_gifs[deck.slug] = assets.preview_gif
            deck_theme_preview_gifs[deck.slug] = assets.theme_preview_gifs

    palette_css = _site_palette_css(site_cfg)
    for section in registry.sections:
        _build_section_page(
            section,
            site_dir,
            env,
            deck_thumbs,
            deck_theme_thumbs,
            deck_preview_gifs,
            deck_theme_preview_gifs,
            deck_dates,
            palette_css,
        )

    _build_index(
        registry,
        site_dir,
        env,
        deck_thumbs,
        deck_theme_thumbs,
        deck_preview_gifs,
        deck_theme_preview_gifs,
        deck_date_infos,
        deck_dates,
        palette_css,
    )


def _date_info_from_date(value: dt.date, *, source: str) -> _DeckDateInfo:
    timestamp = dt.datetime.combine(value, dt.time.min, tzinfo=dt.UTC)
    return _DeckDateInfo(
        value=value,
        timestamp=timestamp.timestamp(),
        label=_format_deck_date(value),
        iso=value.isoformat(),
        source=source,
    )


def _date_info_from_datetime(value: dt.datetime, *, source: str) -> _DeckDateInfo:
    if value.tzinfo is None:
        value = value.replace(tzinfo=dt.UTC)
    value = value.astimezone(dt.UTC)
    day = value.date()
    return _DeckDateInfo(
        value=day,
        timestamp=value.timestamp(),
        label=_format_deck_date(day),
        iso=day.isoformat(),
        source=source,
    )


def _format_deck_date(value: dt.date) -> str:
    return f"{value.strftime('%b')} {value.day}, {value.year}"


def _deck_date_info(deck: DeckConfig) -> _DeckDateInfo | None:
    if deck.date is not None:
        return _date_info_from_date(deck.date, source="deck.toml")
    deck_toml = deck.path / "deck.toml"
    if deck_toml.exists():
        return _filesystem_mtime_date(deck_toml, source="deck.toml-mtime")
    return None


def _filesystem_mtime_date(path: Path, *, source: str) -> _DeckDateInfo | None:
    with contextlib.suppress(OSError):
        return _date_info_from_datetime(
            dt.datetime.fromtimestamp(path.stat().st_mtime, dt.UTC),
            source=source,
        )
    return None


def _latest_section(
    registry: SectionedRegistry,
    deck_date_infos: dict[str, _DeckDateInfo | None] | None = None,
    *,
    limit: int = 12,
) -> Section | None:
    def sort_key(deck: DeckConfig) -> float:
        if deck_date_infos is not None:
            info = deck_date_infos.get(deck.slug)
            return info.timestamp if info is not None else 0.0
        return 0.0

    decks = sorted(registry.all_decks, key=sort_key, reverse=True)
    if not decks:
        return None
    return Section(
        config=SectionConfig(
            slug="latest",
            title="Latest decks",
            blurb="Newest work first.",
            order=-1,
        ),
        decks=tuple(decks[:limit]),
    )
