"""Build the full static portal under `site/`.

Pipeline:

1. Load `SiteConfig` (committed `site.toml` merged with env overrides).
2. Discover every section + deck via `simplex.deck.registry.discover`.
3. For each deck:
   - render videos via manim-slides (skipped when cached or `render=False`),
   - export PDF (best-effort, swallows manim-slides errors in test mode),
   - parse the per-scene JSON manifest into `SlideRef`s,
   - generate thumbnails from the rendered videos,
   - emit `slides.html` from our own RevealJS template,
   - render `notes.md` through markdown-it with the `[slide:N]` plugin,
   - write `index.html` for the deck page.
4. Write the home `index.html` (carousel per section) plus one
   `sections/<slug>/index.html` page per section.
5. Copy vendored static assets (CSS, fonts, RevealJS, viewer.js).
"""

import contextlib
import shutil
import subprocess
from pathlib import Path
from typing import Any, cast

from jinja2 import Environment, PackageLoader, select_autoescape

from simplex.deck.config import DeckConfig
from simplex.deck.registry import Section, SectionedRegistry, discover
from simplex.render import cache, html, manifest, pdf, runner, thumbnail
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

    # Jinja2's stub types `globals` against the built-in defaults; widen so we
    # can register a callable and a SiteConfig as template-level names.
    globals_: dict[str, Any] = cast(dict[str, Any], env.globals)
    globals_["static"] = static
    globals_["site"] = site_cfg
    return env


def _copy_static(site_dir: Path) -> None:
    """Copy bundled static assets into `site/static/`.

    Vendored runtime assets (tailwind, katex, reveal.js) are fetched on demand
    so the build is self-bootstrapping on machines without `scripts/vendor.sh`.
    """
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
    cache_dir: Path,
    *,
    render: bool,
    force: bool = False,
    scenes: tuple[str, ...] = (),
) -> None:
    if not render:
        return
    # When `scenes` is provided at the build level, intersect with this deck's
    # actual scene class names: a deck without any of the requested scenes is
    # skipped silently rather than raising on the runner's unknown-scene check.
    deck_scenes = tuple(s for s in scenes if s in deck.scene_class_names)
    if scenes and not deck_scenes:
        return
    partial = bool(deck_scenes)
    if not partial and not force and cache.is_fresh(deck, cache_dir):
        return
    runner.render(deck, output_dir=media_dir, scenes=deck_scenes)
    # PDF export is best-effort: manim-slides convert may fail before assets
    # exist on disk; degrade silently to "no PDF" rather than break the build.
    with contextlib.suppress(subprocess.SubprocessError, FileNotFoundError):
        pdf.export(deck, output_dir=media_dir)
    if partial:
        # The stamp claims "whole deck is fresh"; a partial render doesn't
        # earn that, and a stale stamp would mask the unrendered scenes on
        # the next full build. Drop it so the next non-partial run re-renders.
        cache.clear(deck, cache_dir)
    else:
        cache.mark_fresh(deck, cache_dir)


def _has_pdf(deck: DeckConfig, deck_dir: Path) -> bool:
    return (deck_dir / f"{deck.slug}.pdf").exists()


def _load_bibliography(deck_path: Path) -> Bibliography | None:
    """Return the deck's parsed `refs.bib`, or `None` when absent."""
    refs = deck_path / "refs.bib"
    return Bibliography.load(refs) if refs.exists() else None


def _has_notes_pdf(deck_dir: Path) -> bool:
    return (deck_dir / "notes.pdf").exists()


def _site_thumb(deck: DeckConfig, deck_out: Path, thumbs: dict[int, Path]) -> str | None:
    """Return the cover thumbnail (slide 0) for a deck card, if any."""
    first = thumbs.get(0)
    if first is None:
        return None
    if first.is_absolute():
        try:
            first = first.relative_to(deck_out)
        except ValueError:
            return None
    return first.as_posix()


def _build_deck(
    deck: DeckConfig,
    *,
    site_dir: Path,
    cache_dir: Path,
    site_cfg: SiteConfig,
    env: Environment,
    render: bool,
    force: bool = False,
    scenes: tuple[str, ...] = (),
) -> str | None:
    """Render one deck. Returns the cover thumbnail href (relative)."""
    deck_out = site_dir / "decks" / deck.slug
    deck_out.mkdir(parents=True, exist_ok=True)

    _maybe_render(deck, deck_out, cache_dir, render=render, force=force, scenes=scenes)

    deck_manifest = manifest.build_manifest(deck, media_dir=deck_out)
    thumbs = thumbnail.generate(
        deck,
        deck_manifest,
        site_deck_dir=deck_out,
        cache_dir=cache_dir,
    )
    # Attach thumbnails back to the slide refs (lightweight rebuild).
    enriched = tuple(
        slide.model_copy(update={"thumbnail": thumbs.get(slide.index)})
        for slide in deck_manifest.slides
    )

    html.render_html(
        deck,
        deck_manifest.model_copy(update={"slides": enriched}),
        output_dir=deck_out,
        static_prefix=site_cfg.url("static"),
    )

    notes_md = deck.path / "notes.md"
    notes_html = ""
    if notes_md.exists():
        bib = _load_bibliography(deck.path)
        notes_html = notes.render(notes_md, slide_count=len(enriched), bibliography=bib)

    total_seconds = sum(s.duration_s for s in enriched)
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
    )
    (deck_out / "index.html").write_text(page, encoding="utf-8")
    return _site_thumb(deck, deck_out, thumbs)


def _build_section_page(
    section: Section,
    site_dir: Path,
    env: Environment,
    thumbs: dict[str, str | None],
) -> None:
    out = site_dir / "sections" / section.config.slug
    out.mkdir(parents=True, exist_ok=True)
    page = env.get_template("section.html").render(
        section=section,
        thumbs=thumbs,
    )
    (out / "index.html").write_text(page, encoding="utf-8")


def _build_index(
    registry: SectionedRegistry,
    site_dir: Path,
    env: Environment,
    thumbs: dict[str, str | None],
) -> None:
    page = env.get_template("index.html").render(
        registry=registry,
        thumbs=thumbs,
    )
    (site_dir / "index.html").write_text(page, encoding="utf-8")


def build(
    decks_dir: Path,
    site_dir: Path,
    cache_dir: Path,
    *,
    render: bool = True,
    site_cfg: SiteConfig | None = None,
    force: bool = False,
    only: tuple[str, ...] = (),
    scenes: tuple[str, ...] = (),
) -> None:
    """Discover decks, optionally render them, and write the static site.

    Pass `render=False` to skip `manim-slides render` + PDF export -- useful
    in tests that need the HTML scaffolding without invoking Manim.

    `force` skips the freshness cache. `only` filters to those deck slugs.
    `scenes` filters each rendered deck to those scene class names (implies
    a forced partial render).
    """
    site_cfg = site_cfg or SiteConfig.load(repo_root=decks_dir.parent)
    registry = discover(decks_dir, default_section_order=site_cfg.default_section_order)
    site_dir.mkdir(parents=True, exist_ok=True)
    env = _jinja(site_cfg)
    _copy_static(site_dir)

    only_set = set(only)
    deck_thumbs: dict[str, str | None] = {}
    for section in registry.sections:
        for deck in section.decks:
            if only_set and deck.slug not in only_set:
                continue
            deck_thumbs[deck.slug] = _build_deck(
                deck,
                site_dir=site_dir,
                cache_dir=cache_dir,
                site_cfg=site_cfg,
                env=env,
                render=render,
                force=force,
                scenes=scenes,
            )

    for section in registry.sections:
        _build_section_page(section, site_dir, env, deck_thumbs)

    _build_index(registry, site_dir, env, deck_thumbs)
