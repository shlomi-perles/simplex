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
    slides_html: Path


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
    scenes: tuple[str, ...] = (),
    write_last_frame: bool = False,
) -> None:
    if not render:
        return
    deck_scenes = tuple(s for s in scenes if s in deck.scene_class_names)
    if scenes and not deck_scenes:
        return
    runner.render(deck, output_dir=media_dir, scenes=deck_scenes, write_last_frame=write_last_frame)
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
    scenes: tuple[str, ...],
    watch: bool,
    theme_name: str | None = None,
) -> _BuiltVariant:
    output_dir.mkdir(parents=True, exist_ok=True)
    _maybe_render(deck, output_dir, render=render, scenes=scenes)

    manifest = reconcile.build_manifest(deck, media_dir=output_dir)
    thumbs = thumbnail.generate(deck, manifest, site_deck_dir=output_dir, cache_dir=cache_dir)
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
        slides_html=slides_html,
    )


def _has_pdf(deck: DeckConfig, deck_dir: Path) -> bool:
    return (deck_dir / filenames.pdf_name(deck, "slides")).exists()


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
    scenes: tuple[str, ...] = (),
    theme_selection: SlideThemeSelection = "all",
    watch: bool = False,
) -> tuple[str | None, str | None]:
    """Render one deck. Returns ``(cover thumbnail, carousel gif)`` hrefs."""
    deck_out = site_dir / "decks" / deck.slug
    deck_out.mkdir(parents=True, exist_ok=True)

    slide_theme_config = themes.resolve_slide_themes(deck, site_cfg.slide_themes)
    slide_theme_mode = "true" if slide_theme_config.enabled else "filter"
    available_slide_themes: tuple[SlideThemeVariant, ...]
    default_slide_theme: SlideThemeVariant
    slide_theme_iframes: dict[str, str] = {}
    slide_theme_versions: dict[str, str] = {}
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
                scenes=scenes,
                theme_name=themed_deck.theme,
                watch=watch,
            )
            built_by_variant[variant] = built
            slide_theme_iframes[variant] = (Path("themes") / variant / "slides.html").as_posix()
            slide_theme_versions[variant] = _file_version(built.slides_html)

        default_built = built_by_variant[default_slide_theme]
        _copy_default_slides_pdf(default_built.deck, default_built.output_dir, deck_out)
        preview_gif = thumbnail.generate_carousel_gif(
            default_built.deck,
            default_built.manifest,
            site_deck_dir=default_built.output_dir,
            cache_dir=deck_out,
        )
        if preview_gif is not None:
            preview_gif_href = (Path("themes") / default_slide_theme / preview_gif).as_posix()
        slides = _build_slide_views(
            default_built.manifest,
            default_variant=default_slide_theme,
            variant_thumbs={variant: built.thumbs for variant, built in built_by_variant.items()},
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
            scenes=scenes,
            watch=watch,
        )
        preview_gif = thumbnail.generate_carousel_gif(
            deck,
            built.manifest,
            site_deck_dir=deck_out,
            cache_dir=deck_out,
        )
        preview_gif_href = preview_gif.as_posix() if preview_gif is not None else None
        slides = _build_slide_views(
            built.manifest,
            default_variant=None,
            variant_thumbs={},
        )
        slide_theme_iframes["dark"] = "slides.html"
        slide_theme_iframes["light"] = "slides.html"
        slide_theme_versions["dark"] = _file_version(built.slides_html)
        slide_theme_versions["light"] = slide_theme_versions["dark"]

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

    page = env.get_template("deck.html").render(
        deck=deck,
        slides=slides,
        slide_count=len(slides),
        total_duration_min=total_minutes,
        has_pdf=_has_pdf(deck, deck_out),
        has_notes_pdf=_has_notes_pdf(deck, deck_out),
        slides_pdf_name=filenames.pdf_name(deck, "slides"),
        notes_pdf_name=filenames.pdf_name(deck, "note"),
        notes_html=notes_html,
        palette_css=render_web_css(
            deck.resolved_web_palette(), code_style=deck.resolved_notes_code_style()
        ),
        slide_theme_mode=slide_theme_mode,
        available_slide_themes=available_slide_themes,
        default_slide_theme=default_slide_theme,
        slide_theme_iframes=slide_theme_iframes,
        slide_theme_versions=slide_theme_versions,
    )
    (deck_out / "index.html").write_text(page, encoding="utf-8")
    cover = slides[0].thumbnail if slides else None
    return (cover, preview_gif_href)


def _build_section_page(
    section: Section,
    site_dir: Path,
    env: Environment,
    thumbs: dict[str, str | None],
    preview_gifs: dict[str, str | None],
    deck_dates: dict[str, str],
    palette_css: str,
) -> None:
    out = site_dir / "sections" / section.config.slug
    out.mkdir(parents=True, exist_ok=True)
    page = env.get_template("section.html").render(
        section=section,
        thumbs=thumbs,
        preview_gifs=preview_gifs,
        deck_dates=deck_dates,
        palette_css=palette_css,
    )
    (out / "index.html").write_text(page, encoding="utf-8")


def _build_index(
    registry: SectionedRegistry,
    site_dir: Path,
    env: Environment,
    thumbs: dict[str, str | None],
    preview_gifs: dict[str, str | None],
    deck_dates: dict[str, str],
    palette_css: str,
) -> None:
    page = env.get_template("index.html").render(
        registry=registry,
        latest_section=_latest_section(registry),
        thumbs=thumbs,
        preview_gifs=preview_gifs,
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
    deck_preview_gifs: dict[str, str | None] = {}
    deck_dates = {deck.slug: _deck_created_label(deck) for deck in registry.all_decks}
    for section in registry.sections:
        for deck in section.decks:
            if only_set and deck.slug not in only_set:
                continue
            deck_thumbs[deck.slug], deck_preview_gifs[deck.slug] = _build_deck(
                deck,
                site_dir=site_dir,
                site_cfg=site_cfg,
                env=env,
                render=render,
                scenes=scenes,
                theme_selection=theme_selection,
                watch=watch,
            )

    site_palette_css = _site_palette_css(site_cfg)
    for section in registry.sections:
        _build_section_page(
            section,
            site_dir,
            env,
            deck_thumbs,
            deck_preview_gifs,
            deck_dates,
            site_palette_css,
        )

    _build_index(
        registry,
        site_dir,
        env,
        deck_thumbs,
        deck_preview_gifs,
        deck_dates,
        site_palette_css,
    )
