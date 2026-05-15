"""Simplex CLI -- new | render | build | serve | clean | doctor | thumbs."""

import contextlib
import http.server
import os
import shutil
import socketserver
import subprocess
from pathlib import Path

import typer
from rich.console import Console

from simplex.deck.registry import discover
from simplex.deck.scaffold import scaffold as deck_scaffold
from simplex.render import cache, pdf, runner, thumbnail
from simplex.web.builder import build as build_site
from simplex.web.site_config import SiteConfig

app = typer.Typer(help="Simplex -- Manim-slides framework with a generated portal.")
console = Console()

_DECKS = Path("decks")
_SITE = Path("site")
_CACHE = Path(".simplex_cache")


@app.command()
def new(target: str) -> None:
    """Scaffold a new deck.

    `simplex new <slug>` creates `decks/<slug>/` (featured section).
    `simplex new <section>/<slug>` creates `decks/<section>/<slug>/`.
    """
    dest = deck_scaffold(target, _DECKS)
    console.print(f"[green]Created[/green] {dest}")


@app.command()
def render(
    slug: str,
    force: bool = typer.Option(False, "--force", help="Ignore the freshness cache and re-render."),
    scene: list[str] = typer.Option(
        None,
        "--scene",
        help="Re-render only this scene class. Repeatable. Implies --force.",
    ),
) -> None:
    """Render a single deck."""
    site_cfg = SiteConfig.load()
    registry = discover(_DECKS, default_section_order=site_cfg.default_section_order)
    deck = registry.find_deck(slug)
    if deck is None:
        raise typer.BadParameter(f"unknown deck: {slug}")
    scenes = tuple(scene or ())
    partial = bool(scenes)
    out = _SITE / "decks" / deck.slug
    out.mkdir(parents=True, exist_ok=True)

    if not partial and not force and cache.is_fresh(deck, _CACHE):
        console.print(
            f"[yellow]cached[/yellow] {deck.slug} -- pass --force or --scene to re-render"
        )
        return

    try:
        runner.render(deck, output_dir=out, scenes=scenes)
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc

    with contextlib.suppress(subprocess.SubprocessError, FileNotFoundError):
        pdf.export(deck, output_dir=out)

    if partial:
        cache.clear(deck, _CACHE)
    else:
        cache.mark_fresh(deck, _CACHE)
    console.print(f"[green]Rendered[/green] {deck.slug} -> {out}")


@app.command()
def thumbs(slug: str) -> None:
    """Regenerate thumbnails for a single deck."""
    site_cfg = SiteConfig.load()
    registry = discover(_DECKS, default_section_order=site_cfg.default_section_order)
    deck = registry.find_deck(slug)
    if deck is None:
        raise typer.BadParameter(f"unknown deck: {slug}")
    out = _SITE / "decks" / deck.slug
    written = thumbnail.regenerate(deck, media_dir=out, cache_dir=_CACHE)
    console.print(f"[green]Wrote[/green] {len(written)} thumbnails for {deck.slug}")


@app.command()
def build(
    force: bool = typer.Option(False, "--force", help="Ignore the freshness cache for every deck."),
    only: list[str] = typer.Option(None, "--only", help="Only build this deck slug. Repeatable."),
    scene: list[str] = typer.Option(
        None,
        "--scene",
        help="Re-render only this scene class on every selected deck. Implies --force.",
    ),
) -> None:
    """Build the full static portal under `site/`."""
    build_site(
        _DECKS,
        _SITE,
        _CACHE,
        force=force,
        only=tuple(only or ()),
        scenes=tuple(scene or ()),
    )
    console.print(f"[green]Built[/green] {_SITE}")


@app.command()
def serve(port: int = 8000) -> None:
    """Serve `site/` via the stdlib HTTP server."""
    if not _SITE.exists():
        raise typer.BadParameter("site/ does not exist -- run `simplex build` first")
    os.chdir(_SITE)
    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", port), handler) as httpd:
        console.print(f"Serving http://localhost:{port}")
        httpd.serve_forever()


@app.command()
def clean(
    deck: list[str] = typer.Option(
        None,
        "--deck",
        help="Only clean these deck slugs (site/decks/<slug>/ + cache stamp + thumbnails).",
    ),
) -> None:
    """Remove `site/`, `media/`, and the render cache.

    With `--deck <slug>` (repeatable), only that deck's site output, cache
    stamp, and thumbnail cache are removed; other decks survive.
    """
    if deck:
        site_cfg = SiteConfig.load()
        registry = discover(_DECKS, default_section_order=site_cfg.default_section_order)
        for slug in deck:
            d = registry.find_deck(slug)
            if d is None:
                raise typer.BadParameter(f"unknown deck: {slug}")
            site_deck = _SITE / "decks" / d.slug
            if site_deck.exists():
                shutil.rmtree(site_deck)
                console.print(f"removed {site_deck}")
            cache.clear(d, _CACHE)
            thumbs_dir = _CACHE / "thumbnails" / d.slug
            if thumbs_dir.exists():
                shutil.rmtree(thumbs_dir)
                console.print(f"removed {thumbs_dir}")
            console.print(f"[green]Cleaned[/green] {d.slug}")
        return

    for target in (_SITE, Path("media"), _CACHE):
        if target.exists():
            shutil.rmtree(target)
            console.print(f"removed {target}")


@app.command()
def doctor() -> None:
    """Verify required system binaries are reachable on PATH."""
    required = ("latex", "ffmpeg", "manim", "manim-slides")
    ok = True
    for tool in required:
        found = shutil.which(tool)
        if found:
            console.print(f"[green]ok[/green]   {tool} -> {found}")
        else:
            console.print(f"[red]MISSING[/red] {tool}")
            ok = False
    raise typer.Exit(code=0 if ok else 1)


if __name__ == "__main__":
    app()
