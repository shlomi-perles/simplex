"""Build the full static portal under ``site/``.

Pipeline (per deck):

1. ``render.runner.render`` (subprocess, skipped when ``render=False``).
2. ``render.pdf.export`` (best-effort).
3. ``render.reconcile.build_manifest`` reads native section JSON +
   manim-slides PresentationConfig -> main/sub tree.
4. ``render.thumbnail.generate`` per main slide (default rule: second-to-last
   subsection's last frame).
5. ``render.html.render_html`` renders our custom RevealJS template with
   the reconciled tree + palette CSS.
6. ``web.notes.render`` runs ``notes.md`` through markdown-it.
7. Write ``index.html`` for the deck page.

No render cache. Manim's per-animation cache + ``save_sections=True``
(applied by the plugin) gives slide-level incrementality for free.
"""

import contextlib
import hashlib
import shutil
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime, time
from pathlib import Path
from typing import Any, cast

from jinja2 import Environment, PackageLoader, select_autoescape

from simplex.deck.config import DeckConfig, SlideThemeSelection, SlideThemeVariant
from simplex.deck.registry import Section, SectionedRegistry, discover
from simplex.deck.section import SectionConfig
from simplex.manifest import DeckManifest
from simplex.render import filenames, html, notes_pdf, pdf, reconcile, runner, themes, thumbnail
from simplex.theme.web_css import render_web_css
from simplex.web import notes, vendor
from simplex.web.bibliography import Bibliography
from simplex.web.site_config import SiteConfig


@dataclass(frozen=True, slots=True)
class _SlideView:
    index: int
    scene: str
    name: str
    duration_s: float
    thumbnail: str | None
    theme_thumbnails: dict[str, str]


@dataclass(frozen=True, slots=True)
class _BuiltVariant:
    variant: SlideThemeVariant
    deck: DeckConfig
    output_dir: Path
    manifest: DeckManifest
    thumbs: dict[int, Path]
    player_frames: dict[tuple[int, int], dict[str, Path]]
    slides_html: Path


@dataclass(frozen=True, slots=True)
class _DeckCardAssets:
    thumbnail: str | None
    theme_thumbnails: dict[str, str]
    preview_gif: str | None
    theme_preview_gifs: dict[str, str]


def _static_source_dir() -> Path:
    return Path(__file__).parent / "static"


def _file_version(path: Path) -> str:
    """Short content hash for cache-busting generated asset URLs."""
    if not path.exists() or not path.is_file():
        return ""
    digest = hashlib.blake2s(digest_size=6)
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
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
    """Copy bundled static assets into ``site/static/``."""
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


def _maybe_render(
    deck: DeckConfig,
    media_dir: Path,
    *,
    render: bool,
    manim_args: tuple[str, ...] = (),
    scenes: tuple[str, ...] = (),
    write_last_frame: bool = False,
) -> None:
    if not render:
        return
    deck_scenes = tuple(s for s in scenes if s in deck.scene_class_names)
    if scenes and not deck_scenes:
        return
    runner.render(
        deck,
        output_dir=media_dir,
        manim_args=manim_args,
        scenes=deck_scenes,
        write_last_frame=write_last_frame,
    )
    with contextlib.suppress(subprocess.SubprocessError, FileNotFoundError, ImportError):
        pdf.export(deck, output_dir=media_dir)


def _build_variant_output(
    deck: DeckConfig,
    *,
    variant: SlideThemeVariant,
    output_dir: Path,
    cache_dir: Path,
    site_cfg: SiteConfig,
    render: bool,
    manim_args: tuple[str, ...],
    scenes: tuple[str, ...],
    watch: bool,
    theme_name: str | None = None,
) -> _BuiltVariant:
    output_dir.mkdir(parents=True, exist_ok=True)
    _maybe_render(deck, output_dir, render=render, manim_args=manim_args, scenes=scenes)

    manifest = reconcile.build_manifest(deck, media_dir=output_dir)
    thumbs = thumbnail.generate(deck, manifest, site_deck_dir=output_dir, cache_dir=cache_dir)
    player_frames = thumbnail.generate_player_frames(
        deck,
        manifest,
        site_deck_dir=output_dir,
        cache_dir=cache_dir,
        extract_missing=True,
    )
    enriched = tuple(
        main.model_copy(update={"thumbnail": thumbs.get(main.index)})
        for main in manifest.main_slides
    )
    slides_html = html.render_html(
        deck,
        manifest.model_copy(update={"main_slides": enriched}),
        output_dir=output_dir,
        static_prefix=site_cfg.url("static"),
        theme_name=theme_name,
        watch=watch,
    )
    return _BuiltVariant(
        variant=variant,
        deck=deck,
        output_dir=output_dir,
        manifest=manifest.model_copy(update={"main_slides": enriched}),
        thumbs=thumbs,
        player_frames=player_frames,
        slides_html=slides_html,
    )


def _has_notes_pdf(deck: DeckConfig, deck_dir: Path) -> bool:
    return (deck_dir / filenames.pdf_name(deck, "note")).exists()


def _slide_ref_labels(
    deck: DeckConfig,
    slides: tuple[Any, ...],
) -> dict[str, tuple[int, str]]:
    """Return label -> ``(index, display label)`` for note slide refs."""
    from simplex.web.slide_ref import label_key

    refs: dict[str, tuple[int, str]] = {}
    for slide in slides:
        index = int(slide.index)
        display = str(slide.name)
        candidates = {
            str(index),
            display,
            label_key(display),
            str(slide.scene),
            label_key(str(slide.scene)),
        }
        override = deck.slides.get(display)
        if override and override.notes_anchor:
            candidates.add(override.notes_anchor)
            candidates.add(label_key(override.notes_anchor))
        for candidate in candidates:
            key = label_key(candidate)
            if key:
                refs.setdefault(key, (index, display))
    return refs


def _load_bibliography(deck_path: Path) -> Bibliography | None:
    refs = deck_path / "refs.bib"
    return Bibliography.load(refs) if refs.exists() else None


def _theme_rel(
    variant: SlideThemeVariant,
    path: Path | None,
) -> Path | None:
    """Convert a variant-local relative path into a deck-page relative path."""
    if path is None:
        return None
    return Path("themes") / variant / path


def _copy_default_slides_pdf(deck: DeckConfig, source_dir: Path, deck_out: Path) -> None:
    """Expose the default variant's slides PDF at the deck root for downloads."""
    source = source_dir / filenames.pdf_name(deck, "slides")
    if not source.exists():
        return
    target = deck_out / source.name
    if not target.exists() or target.stat().st_mtime < source.stat().st_mtime:
        shutil.copy2(source, target)


def _slides_pdf_hrefs(
    deck: DeckConfig,
    deck_out: Path,
    *,
    built_by_variant: dict[SlideThemeVariant, _BuiltVariant] | None = None,
) -> dict[str, str]:
    """Return downloadable slides-PDF hrefs relative to the deck page."""
    root_name = filenames.pdf_name(deck, "slides")
    hrefs: dict[str, str] = {}
    if (deck_out / root_name).exists():
        hrefs["default"] = root_name
    if built_by_variant:
        for variant, built in built_by_variant.items():
            name = filenames.pdf_name(built.deck, "slides")
            if (built.output_dir / name).exists():
                hrefs[variant] = (Path("themes") / variant / name).as_posix()
    return hrefs


def _build_slide_views(
    manifest: DeckManifest,
    *,
    default_variant: SlideThemeVariant | None,
    variant_thumbs: dict[SlideThemeVariant, dict[int, Path]],
) -> tuple[_SlideView, ...]:
    slides: list[_SlideView] = []
    for main in manifest.main_slides:
        per_theme: dict[str, str] = {}
        for variant, thumbs in variant_thumbs.items():
            rel = _theme_rel(variant, thumbs.get(main.index))
            if rel is not None:
                per_theme[variant] = rel.as_posix()
        thumbnail: str | None = None
        if default_variant is not None:
            thumbnail = per_theme.get(default_variant)
        if thumbnail is None and main.thumbnail is not None:
            thumbnail = main.thumbnail.as_posix()
        slides.append(
            _SlideView(
                index=main.index,
                scene=main.scene,
                name=main.name,
                duration_s=main.duration_s,
                thumbnail=thumbnail,
                theme_thumbnails=per_theme,
            )
        )
    return tuple(slides)


def _prefixed_path(prefix: str, path: Path | None) -> str | None:
    if path is None:
        return None
    rel = path.as_posix()
    return f"{prefix}/{rel}" if prefix else rel


def _segment_path(main_idx: int, sub_idx: int) -> Path:
    return Path("segments") / f"{main_idx:04d}_{sub_idx:02d}.mp4"


def _variant_main_map(
    built_by_variant: dict[SlideThemeVariant, _BuiltVariant],
) -> dict[SlideThemeVariant, dict[int, Any]]:
    return {
        variant: {main.index: main for main in built.manifest.main_slides}
        for variant, built in built_by_variant.items()
    }


def _sub_at(main: Any, sub_idx: int) -> Any | None:
    subs = tuple(getattr(main, "subsections", ()) or ())
    return subs[sub_idx] if sub_idx < len(subs) else None


def _theme_asset(
    *,
    prefix: str,
    built: _BuiltVariant,
    main: Any,
    sub_idx: int,
) -> dict[str, str | None]:
    sub = _sub_at(main, sub_idx)
    frames = built.player_frames.get((int(main.index), sub_idx), {})
    fallback = built.thumbs.get(int(main.index))
    has_video = sub is not None and sub.video is not None and sub.video.exists()
    first_frame = frames.get("first") if has_video else frames.get("first") or fallback
    last_frame = frames.get("last") or (fallback if has_video else first_frame)
    return {
        "video": _prefixed_path(
            prefix, _segment_path(int(main.index), sub_idx) if has_video else None
        ),
        "firstFrame": _prefixed_path(prefix, first_frame),
        "lastFrame": _prefixed_path(prefix, last_frame),
        "thumbnail": _prefixed_path(prefix, fallback),
    }


def _build_player_manifest(
    *,
    deck: DeckConfig,
    default_manifest: DeckManifest,
    built_by_variant: dict[SlideThemeVariant, _BuiltVariant],
    variant_prefixes: dict[SlideThemeVariant, str],
    available_slide_themes: tuple[SlideThemeVariant, ...],
    default_slide_theme: SlideThemeVariant,
    slide_theme_mode: str,
) -> dict[str, Any]:
    variant_mains = _variant_main_map(built_by_variant)
    slides: list[dict[str, Any]] = []
    for main in default_manifest.main_slides:
        sub_count = max(1, len(main.subsections))
        subslides: list[dict[str, Any]] = []
        for sub_idx in range(sub_count):
            default_sub = _sub_at(main, sub_idx)
            themes_by_variant: dict[str, dict[str, str | None]] = {}
            for variant in available_slide_themes:
                variant_main = variant_mains.get(variant, {}).get(main.index, main)
                themes_by_variant[variant] = _theme_asset(
                    prefix=variant_prefixes.get(variant, ""),
                    built=built_by_variant[variant],
                    main=variant_main,
                    sub_idx=sub_idx,
                )
            subslides.append(
                {
                    "subIndex": sub_idx,
                    "name": str(default_sub.name if default_sub is not None else main.name),
                    "sectionType": str(
                        default_sub.section_type.value
                        if default_sub is not None
                        else main.section_type.value
                    ),
                    "duration": float(
                        default_sub.duration_s if default_sub is not None else main.duration_s
                    ),
                    "themes": themes_by_variant,
                }
            )
        slides.append(
            {
                "mainIndex": int(main.index),
                "scene": str(main.scene),
                "name": str(main.name),
                "duration": float(main.duration_s),
                "subslides": subslides,
            }
        )
    return {
        "deckSlug": deck.slug,
        "mode": slide_theme_mode,
        "defaultTheme": default_slide_theme,
        "availableThemes": tuple(available_slide_themes),
        "slideCount": len(slides),
        "slides": slides,
    }


def _initial_player_frames(
    player_manifest: dict[str, Any],
) -> dict[str, str]:
    slides = player_manifest.get("slides")
    if not isinstance(slides, list) or not slides:
        return {}
    first_slide = slides[0]
    if not isinstance(first_slide, dict):
        return {}
    subslides = first_slide.get("subslides")
    if not isinstance(subslides, list) or not subslides:
        return {}
    first_sub = subslides[0]
    if not isinstance(first_sub, dict):
        return {}
    themes_by_variant = first_sub.get("themes")
    if not isinstance(themes_by_variant, dict):
        return {}
    out: dict[str, str] = {}
    for variant, raw_asset in themes_by_variant.items():
        if not isinstance(variant, str) or not isinstance(raw_asset, dict):
            continue
        frame = (
            raw_asset.get("firstFrame")
            or (None if raw_asset.get("video") else raw_asset.get("lastFrame"))
            or raw_asset.get("thumbnail")
        )
        if isinstance(frame, str) and frame:
            out[variant] = frame
    return out


def _deck_created_timestamp(deck: DeckConfig) -> float:
    """Sort key for "latest" decks: explicit creation date, then file mtime."""
    if deck.created_at is not None:
        return datetime.combine(deck.created_at, time.min, tzinfo=UTC).timestamp()
    toml = deck.path / "deck.toml"
    with contextlib.suppress(OSError):
        return toml.stat().st_mtime
    return 0.0


def _deck_created_label(deck: DeckConfig) -> str:
    if deck.created_at is not None:
        return deck.created_at.strftime("%b %d, %Y")
    toml = deck.path / "deck.toml"
    with contextlib.suppress(OSError):
        return datetime.fromtimestamp(toml.stat().st_mtime, UTC).strftime("%b %d, %Y")
    return ""


def _latest_section(registry: SectionedRegistry, *, limit: int = 12) -> Section | None:
    decks = sorted(registry.all_decks, key=_deck_created_timestamp, reverse=True)
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


def _build_deck(
    deck: DeckConfig,
    *,
    site_dir: Path,
    site_cfg: SiteConfig,
    env: Environment,
    render: bool,
    manim_args: tuple[str, ...] = (),
    scenes: tuple[str, ...] = (),
    theme_selection: SlideThemeSelection = "all",
    watch: bool = False,
) -> _DeckCardAssets:
    """Render one deck and return its homepage/section-card assets."""
    deck_out = site_dir / "decks" / deck.slug
    deck_out.mkdir(parents=True, exist_ok=True)

    slide_theme_config = themes.resolve_slide_themes(deck, site_cfg.slide_themes)
    slide_theme_mode = "true" if slide_theme_config.enabled else "filter"
    available_slide_themes: tuple[SlideThemeVariant, ...]
    default_slide_theme: SlideThemeVariant
    preview_gif_href: str | None = None

    if slide_theme_config.enabled:
        available_slide_themes = themes.selected_variants(slide_theme_config, theme_selection)
        default_slide_theme = slide_theme_config.default_variant(available_slide_themes)
        built_by_variant: dict[SlideThemeVariant, _BuiltVariant] = {}
        for variant in available_slide_themes:
            themed_deck = themes.variant_deck(deck, slide_theme_config, variant)
            variant_dir = themes.variant_output_dir(deck_out, variant)
            built = _build_variant_output(
                themed_deck,
                variant=variant,
                output_dir=variant_dir,
                cache_dir=deck_out,
                site_cfg=site_cfg,
                render=render,
                manim_args=manim_args,
                scenes=scenes,
                theme_name=themed_deck.theme,
                watch=watch,
            )
            built_by_variant[variant] = built

        default_built = built_by_variant[default_slide_theme]
        page_theme_name = default_built.deck.theme
        _copy_default_slides_pdf(default_built.deck, default_built.output_dir, deck_out)
        theme_preview_gifs: dict[str, str] = {}
        for variant, built in built_by_variant.items():
            preview_gif = thumbnail.generate_carousel_gif(
                built.deck,
                built.manifest,
                site_deck_dir=built.output_dir,
                cache_dir=deck_out,
            )
            if preview_gif is not None:
                theme_preview_gifs[variant] = (Path("themes") / variant / preview_gif).as_posix()
        preview_gif_href = theme_preview_gifs.get(default_slide_theme)
        slides = _build_slide_views(
            default_built.manifest,
            default_variant=default_slide_theme,
            variant_thumbs={variant: built.thumbs for variant, built in built_by_variant.items()},
        )
        player_manifest = _build_player_manifest(
            deck=deck,
            default_manifest=default_built.manifest,
            built_by_variant=built_by_variant,
            variant_prefixes={variant: f"themes/{variant}" for variant in built_by_variant},
            available_slide_themes=available_slide_themes,
            default_slide_theme=default_slide_theme,
            slide_theme_mode=slide_theme_mode,
        )
    else:
        available_slide_themes = ("dark", "light")
        default_slide_theme = "dark"
        built = _build_variant_output(
            deck,
            variant="dark",
            output_dir=deck_out,
            cache_dir=deck_out,
            site_cfg=site_cfg,
            render=render,
            manim_args=manim_args,
            scenes=scenes,
            watch=watch,
        )
        page_theme_name = built.deck.theme
        preview_gif = thumbnail.generate_carousel_gif(
            deck,
            built.manifest,
            site_deck_dir=deck_out,
            cache_dir=deck_out,
        )
        preview_gif_href = preview_gif.as_posix() if preview_gif is not None else None
        theme_preview_gifs = {}
        slides = _build_slide_views(
            built.manifest,
            default_variant=None,
            variant_thumbs={},
        )
        built_by_variant = {"dark": built, "light": built}
        player_manifest = _build_player_manifest(
            deck=deck,
            default_manifest=built.manifest,
            built_by_variant=built_by_variant,
            variant_prefixes={"dark": "", "light": ""},
            available_slide_themes=available_slide_themes,
            default_slide_theme=default_slide_theme,
            slide_theme_mode=slide_theme_mode,
        )

    notes_md = deck.path / "notes.md"
    notes_html = ""
    slide_refs = _slide_ref_labels(deck, slides)
    if notes_md.exists():
        bib = _load_bibliography(deck.path)
        notes_html = notes.render(
            notes_md,
            slide_count=len(slides),
            slide_refs=slide_refs,
            bibliography=bib,
            code_style=deck.resolved_notes_code_style(),
        )
        if render:
            with contextlib.suppress(
                subprocess.SubprocessError,
                FileNotFoundError,
                ImportError,
            ):
                notes_pdf.export(
                    deck,
                    notes_md,
                    output_dir=deck_out,
                    slide_refs=slide_refs,
                    bibliography=bib,
                )

    total_seconds = sum(m.duration_s for m in slides)
    total_minutes: int | None = int(total_seconds // 60) if total_seconds > 0 else None
    if deck.duration_minutes is not None:
        total_minutes = deck.duration_minutes
    slides_pdf_hrefs = _slides_pdf_hrefs(
        deck,
        deck_out,
        built_by_variant=built_by_variant if slide_theme_config.enabled else None,
    )

    page = env.get_template("deck.html").render(
        deck=deck,
        slides=slides,
        slide_count=len(slides),
        total_duration_min=total_minutes,
        has_pdf=bool(slides_pdf_hrefs),
        has_notes_pdf=_has_notes_pdf(deck, deck_out),
        slides_pdf_href=slides_pdf_hrefs.get(default_slide_theme)
        or slides_pdf_hrefs.get("default")
        or next(iter(slides_pdf_hrefs.values()), filenames.pdf_name(deck, "slides")),
        slides_pdf_hrefs=slides_pdf_hrefs,
        notes_pdf_name=filenames.pdf_name(deck, "note"),
        notes_html=notes_html,
        palette_css=render_web_css(
            deck.resolved_web_palette(page_theme_name), code_style=deck.resolved_notes_code_style()
        ),
        slide_theme_mode=slide_theme_mode,
        available_slide_themes=available_slide_themes,
        default_slide_theme=default_slide_theme,
        player_manifest=player_manifest,
        initial_player_frames=_initial_player_frames(player_manifest),
    )
    (deck_out / "index.html").write_text(page, encoding="utf-8")
    cover = slides[0].thumbnail if slides else None
    return _DeckCardAssets(
        thumbnail=cover,
        theme_thumbnails=dict(slides[0].theme_thumbnails) if slides else {},
        preview_gif=preview_gif_href,
        theme_preview_gifs=theme_preview_gifs,
    )


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
    deck_dates: dict[str, str],
    palette_css: str,
) -> None:
    page = env.get_template("index.html").render(
        registry=registry,
        latest_section=_latest_section(registry),
        thumbs=thumbs,
        theme_thumbs=theme_thumbs,
        preview_gifs=preview_gifs,
        theme_preview_gifs=theme_preview_gifs,
        deck_dates=deck_dates,
        palette_css=palette_css,
    )
    (site_dir / "index.html").write_text(page, encoding="utf-8")


def _site_palette_css(site_cfg: SiteConfig) -> str:
    """Return CSS for the site-wide palette (uses site_cfg.theme if set, else default)."""
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
    """Discover decks, render them, write the static site."""
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
    deck_dates = {deck.slug: _deck_created_label(deck) for deck in registry.all_decks}
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
                manim_args=manim_args,
                scenes=scenes,
                theme_selection=theme_selection,
                watch=watch,
            )
            deck_thumbs[deck.slug] = assets.thumbnail
            deck_theme_thumbs[deck.slug] = assets.theme_thumbnails
            deck_preview_gifs[deck.slug] = assets.preview_gif
            deck_theme_preview_gifs[deck.slug] = assets.theme_preview_gifs

    site_palette_css = _site_palette_css(site_cfg)
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
            site_palette_css,
        )

    _build_index(
        registry,
        site_dir,
        env,
        deck_thumbs,
        deck_theme_thumbs,
        deck_preview_gifs,
        deck_theme_preview_gifs,
        deck_dates,
        site_palette_css,
    )
