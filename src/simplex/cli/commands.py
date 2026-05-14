"""Simplex CLI -- new | render | build | serve | clean | doctor | thumbs."""

import http.server
import os
import shutil
import socketserver
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
def render(slug: str) -> None:
    """Render a single deck."""
    site_cfg = SiteConfig.load()
    registry = discover(_DECKS, default_section_order=site_cfg.default_section_order)
    deck = registry.find_deck(slug)
    if deck is None:
        raise typer.BadParameter(f"unknown deck: {slug}")
    out = _SITE / "decks" / deck.slug
    out.mkdir(parents=True, exist_ok=True)
    runner.render(deck, output_dir=out)
    pdf.export(deck, output_dir=out)
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
def build() -> None:
    """Build the full static portal under `site/`."""
    build_site(_DECKS, _SITE, _CACHE)
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
def clean() -> None:
    """Remove `site/`, `media/`, and the render cache."""
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
