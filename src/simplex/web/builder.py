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
import shutil
import subprocess
from datetime import UTC, datetime, time
from pathlib import Path
from typing import Any, cast

from jinja2 import Environment, PackageLoader, select_autoescape

from simplex.deck.config import DeckConfig
from simplex.deck.registry import Section, SectionedRegistry, discover
from simplex.deck.section import SectionConfig
from simplex.render import html, pdf, reconcile, runner, thumbnail
from simplex.theme.web_css import render_web_css
from simplex.web import notes, vendor
from simplex.web.bibliography import Bibliography
from simplex.web.site_config import SiteConfig


def _jinja(site_cfg: SiteConfig) -> Environment:
    env = Environment(
        loader=PackageLoader("simplex.web", "templates"),
        autoescape=select_autoescape(["html", "j2"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )

    def static(path: str) -> str:
        return site_cfg.url("static/" + path.lstrip("/"))

    globals_: dict[str, Any] = cast(dict[str, Any], env.globals)
    globals_["static"] = static
    globals_["site"] = site_cfg
    return env


def _copy_static(site_dir: Path) -> None:
    """Copy bundled static assets into ``site/static/``."""
    src = Path(__file__).parent / "static"
    src.mkdir(parents=True, exist_ok=True)
    vendor.ensure(src)
    dst = site_dir / "static"
    dst.mkdir(parents=True, exist_ok=True)
    for entry in src.iterdir():
        if entry.name in {"README.md", ".gitkeep"}:
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


def _has_pdf(deck: DeckConfig, deck_dir: Path) -> bool:
    return (deck_dir / f"{deck.slug}.pdf").exists()


def _has_notes_pdf(deck_dir: Path) -> bool:
    return (deck_dir / "notes.pdf").exists()


def _load_bibliography(deck_path: Path) -> Bibliography | None:
    refs = deck_path / "refs.bib"
    return Bibliography.load(refs) if refs.exists() else None


def _site_thumb(deck_out: Path, thumbs: dict[int, Path]) -> str | None:
    """Return the cover thumbnail (main slide #1) for a deck card."""
    first = thumbs.get(1)
    if first is None:
        return None
    if first.is_absolute():
        try:
            first = first.relative_to(deck_out)
        except ValueError:
            return None
    return first.as_posix()


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
    watch: bool = False,
) -> tuple[str | None, str | None]:
    """Render one deck. Returns ``(cover thumbnail, carousel gif)`` hrefs."""
    deck_out = site_dir / "decks" / deck.slug
    deck_out.mkdir(parents=True, exist_ok=True)

    _maybe_render(deck, deck_out, render=render, scenes=scenes)

    manifest = reconcile.build_manifest(deck, media_dir=deck_out)
    thumbs = thumbnail.generate(deck, manifest, site_deck_dir=deck_out, cache_dir=deck_out)
    preview_gif = thumbnail.generate_carousel_gif(
        deck,
        manifest,
        site_deck_dir=deck_out,
        cache_dir=deck_out,
    )

    enriched = tuple(
        main.model_copy(update={"thumbnail": thumbs.get(main.index)})
        for main in manifest.main_slides
    )

    html.render_html(
        deck,
        manifest.model_copy(update={"main_slides": enriched}),
        output_dir=deck_out,
        static_prefix=site_cfg.url("static"),
        watch=watch,
    )

    notes_md = deck.path / "notes.md"
    notes_html = ""
    if notes_md.exists():
        bib = _load_bibliography(deck.path)
        notes_html = notes.render(notes_md, slide_count=len(enriched), bibliography=bib)

    total_seconds = sum(m.duration_s for m in enriched)
    total_minutes: int | None = int(total_seconds // 60) if total_seconds > 0 else None
    if deck.duration_minutes is not None:
        total_minutes = deck.duration_minutes

    page = env.get_template("deck.html").render(
        deck=deck,
        slides=enriched,
        slide_count=len(enriched),
        total_duration_min=total_minutes,
        has_pdf=_has_pdf(deck, deck_out),
        has_notes_pdf=_has_notes_pdf(deck_out),
        notes_html=notes_html,
        palette_css=render_web_css(deck.resolved_web_palette()),
    )
    (deck_out / "index.html").write_text(page, encoding="utf-8")
    return (
        _site_thumb(deck_out, thumbs),
        preview_gif.as_posix() if preview_gif is not None else None,
    )


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

    theme_name = getattr(site_cfg, "theme", None) or "dastimator_dark"
    return render_web_css(get_theme(theme_name).web_palette)


def build(
    decks_dir: Path,
    site_dir: Path,
    *,
    render: bool = True,
    site_cfg: SiteConfig | None = None,
    only: tuple[str, ...] = (),
    scenes: tuple[str, ...] = (),
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
