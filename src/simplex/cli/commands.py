"""Simplex CLI -- new | init | render | build | serve | test | clean | doctor."""

import asyncio
import contextlib
import http.server
import shutil
import socketserver
import subprocess
import sys
import threading
from collections.abc import Iterable
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from simplex.deck.registry import discover
from simplex.deck.scaffold import scaffold as deck_scaffold
from simplex.render import pdf, runner
from simplex.web.builder import build as build_site
from simplex.web.site_config import SiteConfig

app = typer.Typer(help="Simplex -- Manim-slides framework with a generated portal.")
console = Console()

_DECKS = Path("decks")
_SITE = Path("site")

# Reload signaling for `simplex serve --watch`.
_RELOAD_EVENT = threading.Event()


@app.command()
def new(target: str) -> None:
    """Scaffold a new deck.

    ``simplex new <slug>`` creates ``decks/<slug>/`` (featured section).
    ``simplex new <section>/<slug>`` creates ``decks/<section>/<slug>/``.
    """
    dest = deck_scaffold(target, _DECKS)
    console.print(f"[green]Created[/green] {dest}")


@app.command()
def init(
    target_dir: Annotated[
        Path | None,
        typer.Argument(
            help="Directory to create. Default: prompt + git clone the template.",
        ),
    ] = None,
) -> None:
    """Scaffold a new lectures repo from ``shlomi-perles/simplex-lectures-template``.

    Requires the ``gh`` CLI for full template integration; falls back to
    ``git clone`` of the public template otherwise.
    """
    template_repo = "shlomi-perles/simplex-lectures-template"
    if target_dir is None:
        target_dir = Path(typer.prompt("New repo directory name"))
    if target_dir.exists():
        raise typer.BadParameter(f"{target_dir} already exists")

    gh_path = shutil.which("gh")
    if gh_path is not None:
        repo_name = typer.prompt(
            f"GitHub repo to create (default: {target_dir.name})",
            default=target_dir.name,
        )
        subprocess.run(
            [
                gh_path,
                "repo",
                "create",
                repo_name,
                "--template",
                template_repo,
                "--clone",
                "--private",
            ],
            check=True,
        )
        console.print(f"[green]Created[/green] {repo_name} from {template_repo}")
        return

    git_path = shutil.which("git")
    if git_path is None:
        raise typer.BadParameter("neither `gh` nor `git` is available on PATH")
    subprocess.run(
        [git_path, "clone", f"https://github.com/{template_repo}.git", str(target_dir)],
        check=True,
    )
    shutil.rmtree(target_dir / ".git", ignore_errors=True)
    console.print(
        f"[green]Cloned[/green] template into {target_dir}. "
        "Run `git init && git add . && git commit -m initial` inside it next."
    )


@app.command()
def render(
    target: str,
    scene: Annotated[
        list[str] | None,
        typer.Option(
            "--scene",
            help="Re-render only this scene class. Repeatable.",
        ),
    ] = None,
) -> None:
    """Render a single deck.

    Triple-syntax targets accepted:

    - ``slug``                       full deck
    - ``slug::SceneClass``           one scene (alias for ``--scene SceneClass``)
    - ``slug::SceneClass::MainName`` reserved; for now renders the whole scene
    """
    slug, _, scene_spec = target.partition("::")
    site_cfg = SiteConfig.load()
    registry = discover(_DECKS, default_section_order=site_cfg.default_section_order)
    deck = registry.find_deck(slug)
    if deck is None:
        raise typer.BadParameter(f"unknown deck: {slug}")

    scene_filter: tuple[str, ...] = tuple(scene or ())
    if scene_spec:
        scene_name, _, _main = scene_spec.partition("::")
        scene_filter = (*scene_filter, scene_name)

    out = _SITE / "decks" / deck.slug
    out.mkdir(parents=True, exist_ok=True)

    try:
        runner.render(deck, output_dir=out, scenes=scene_filter)
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc

    with contextlib.suppress(subprocess.SubprocessError, FileNotFoundError, ImportError):
        pdf.export(deck, output_dir=out)

    console.print(f"[green]Rendered[/green] {deck.slug} -> {out}")


@app.command()
def build(
    only: Annotated[
        list[str] | None,
        typer.Option("--only", help="Only build this deck slug. Repeatable."),
    ] = None,
    scene: Annotated[
        list[str] | None,
        typer.Option(
            "--scene",
            help="Re-render only this scene class on every selected deck.",
        ),
    ] = None,
    no_render: Annotated[
        bool,
        typer.Option("--no-render", help="Skip rendering; only rebuild HTML/portal."),
    ] = False,
) -> None:
    """Build the full static portal under ``site/``."""
    build_site(
        _DECKS,
        _SITE,
        render=not no_render,
        only=tuple(only or ()),
        scenes=tuple(scene or ()),
    )
    console.print(f"[green]Built[/green] {_SITE}")


@app.command()
def test(
    only: Annotated[
        list[str] | None,
        typer.Option("--only", help="Only test this deck slug. Repeatable."),
    ] = None,
) -> None:
    """Smoke-render every deck with ``--write_last_frame --quality l``.

    Used in CI: catches scene-construction errors without paying for full
    video encoding. Exits non-zero on the first deck that fails to render.
    """
    site_cfg = SiteConfig.load()
    registry = discover(_DECKS, default_section_order=site_cfg.default_section_order)
    only_set = set(only or ())

    failures: list[tuple[str, str]] = []
    for section in registry.sections:
        for deck in section.decks:
            if only_set and deck.slug not in only_set:
                continue
            out = _SITE / "decks" / deck.slug
            try:
                runner.render(deck, output_dir=out, write_last_frame=True)
                console.print(f"[green]ok[/green]   {deck.slug}")
            except (subprocess.CalledProcessError, ValueError) as exc:
                failures.append((deck.slug, str(exc)))
                console.print(f"[red]FAIL[/red] {deck.slug}: {exc}")

    if failures:
        raise typer.Exit(code=1)


@app.command()
def serve(
    port: Annotated[int, typer.Option(help="Port to serve on.")] = 8000,
    watch: Annotated[
        bool,
        typer.Option(
            "--watch/--no-watch",
            help="Watch decks/ + src/ and reload the browser on save.",
        ),
    ] = False,
) -> None:
    """Serve ``site/`` via the stdlib HTTP server.

    With ``--watch``, also runs a watchfiles loop that re-runs the build on
    every save and pushes an SSE event so open browser tabs reload.
    """
    if not _SITE.exists():
        raise typer.BadParameter("site/ does not exist -- run `simplex build` first")

    handler_cls = _make_handler(_SITE)
    server = _SimplexTCPServer(("", port), handler_cls)
    console.print(f"Serving http://localhost:{port}")

    server_thread: threading.Thread | None = None
    try:
        if watch:
            server_thread = threading.Thread(target=server.serve_forever, daemon=True)
            server_thread.start()
            asyncio.run(_watch_loop())
        else:
            server.serve_forever(poll_interval=0.2)
    except KeyboardInterrupt:
        console.print("\n[yellow]stopping[/yellow]")
    finally:
        if server_thread is not None:
            server.shutdown()
            server_thread.join(timeout=2)
        server.server_close()


class _SimplexTCPServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


def _make_handler(site_dir: Path) -> type[http.server.BaseHTTPRequestHandler]:
    """Return a request handler that serves files + an SSE endpoint."""

    class _Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args: object, **kwargs: object) -> None:
            super().__init__(*args, directory=str(site_dir), **kwargs)  # type: ignore[arg-type]

        def do_GET(self) -> None:
            if self.path == "/_simplex/events":
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.send_header("Cache-Control", "no-cache")
                self.send_header("Connection", "keep-alive")
                self.end_headers()
                self._stream_events()
                return
            super().do_GET()

        def _stream_events(self) -> None:
            try:
                while True:
                    if _RELOAD_EVENT.wait(timeout=30):
                        _RELOAD_EVENT.clear()
                        self.wfile.write(b"event: reload\ndata: 1\n\n")
                    else:
                        self.wfile.write(b": keepalive\n\n")
                    self.wfile.flush()
            except BrokenPipeError:
                pass
            except ConnectionResetError:
                pass

        def log_message(self, format: str, *args: object) -> None:
            pass  # quiet by default

    return _Handler


async def _watch_loop() -> None:
    """Watchfiles + rebuild + broadcast SSE reload on every change."""
    try:
        from watchfiles import awatch
    except ImportError as exc:
        raise typer.BadParameter(
            "watchfiles is required for --watch; install with `uv sync`"
        ) from exc

    targets = [p for p in (Path("decks"), Path("src") / "simplex") if p.exists()]
    console.print(f"[yellow]watching[/yellow] {', '.join(str(t) for t in targets)}")

    async for changes in awatch(*targets, debounce=200):
        affected = sorted(_affected_deck_slugs(changes))
        if not affected:
            continue
        console.print(f"[yellow]reload[/yellow] {', '.join(affected)}")
        try:
            build_site(_DECKS, _SITE, only=tuple(affected), watch=True)
            _RELOAD_EVENT.set()
        except Exception as exc:
            console.print(f"[red]build failed[/red]: {exc}")


def _affected_deck_slugs(changes: Iterable[tuple[object, str]]) -> set[str]:
    """Map watchfiles change paths to the deck slugs they affect.

    A change under ``decks/<slug>/...`` affects that slug. A change under
    ``src/simplex/...`` affects every deck (return empty -> caller rebuilds all).
    """
    slugs: set[str] = set()
    src_changed = False
    for _, path in changes:
        parts = Path(path).resolve().relative_to(Path.cwd().resolve(), walk_up=True).parts
        if len(parts) >= 2 and parts[0] == "decks":
            slugs.add(parts[1])
        elif len(parts) >= 2 and parts[0] == "src":
            src_changed = True
    if src_changed:
        slugs = set()  # signals "rebuild everything"
    return slugs


@app.command()
def clean(
    deck: Annotated[
        list[str] | None,
        typer.Option(
            "--deck",
            help="Only clean these deck slugs (site/decks/<slug>/).",
        ),
    ] = None,
) -> None:
    """Remove ``site/`` and ``media/``.

    With ``--deck <slug>`` (repeatable), only that deck's output is removed.
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
            console.print(f"[green]Cleaned[/green] {d.slug}")
        return

    for target in (_SITE, Path("media")):
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
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    app()
