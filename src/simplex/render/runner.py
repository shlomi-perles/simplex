"""Invoke ``manim-slides render`` via subprocess.

Projects usually keep shared Manim defaults in a repo-root ``manim.cfg``.
A deck may add its own ``manim.cfg``; when both files exist Simplex gives
Manim a temporary merged config where deck-local keys override matching
global keys and unrelated sections/options are preserved. The plugin
entry-point applies theme defaults at ``import manim`` time, while Manim's
own CLI/config parser owns render flags such as quality, caching, frame size,
and preview options. Simplex forwards user Manim args unchanged and appends
only the invariants needed for generated-site layout and section
reconciliation.

The runner re-introduces the ``SIMPLEX_THEME`` env var purely to *select*
which preset the plugin activates -- Python's ``ContextVar`` doesn't
traverse the ``subprocess`` boundary, so without the env var every render
falls back to ``SIMPLEX_DARK`` regardless of what the deck's ``deck.toml``
declares.

We still spawn a subprocess (not in-process) for three reasons: clean
SIGINT, OOM isolation, and per-deck ``manim.config`` isolation.

We run with ``cwd=deck.path`` so relative scene assets behave like a normal
Manim project. ``SIMPLEX_SLIDES_DIR`` points Simplex slide classes at
``<output_dir>/slides`` for manim-slides PresentationConfig output; manim's
section + video output goes to ``<output_dir>/videos/<src_stem>/<q>/...`` via
forced ``--media_dir``.
"""

import configparser
import contextlib
import os
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Generator
from pathlib import Path

from simplex.deck.config import DeckConfig, ResolvedSceneGroup
from simplex.render._warnings import append_pythonwarnings_filter


def _filter_groups(
    groups: tuple[ResolvedSceneGroup, ...],
    scenes: tuple[str, ...],
) -> tuple[ResolvedSceneGroup, ...]:
    """Keep only entries whose class name is in ``scenes``. Drop empty groups."""
    wanted = set(scenes)
    available = {name for group in groups for name in group.scene_names}
    unknown = wanted - available
    if unknown:
        raise ValueError(
            f"unknown scene name(s): {sorted(unknown)!r}; known: {sorted(available)!r}"
        )
    filtered: list[ResolvedSceneGroup] = []
    for group in groups:
        names = group.scene_names
        kept = tuple(n for n in names if n in wanted)
        if kept:
            filtered.append(
                ResolvedSceneGroup(
                    source_file=group.source_file,
                    scene_names=kept,
                    renderer=group.renderer,
                )
            )
    return tuple(filtered)


# Environment variables that can redirect a child interpreter at (or before)
# import time to a *different* Python environment than the one running Simplex.
# We drop them from render subprocesses so each manim render is hermetic and
# resolves packages only from Simplex's own venv -- otherwise an activated conda
# base or foreign virtualenv in the caller's shell (e.g. a stray
# ``PYTHONPATH=...\miniforge3`` that ``uv run`` forwards unchanged) can shadow
# the venv's manim/numpy/PIL and cause cross-environment import failures.
_ENV_OVERRIDE_KEYS = ("PYTHONPATH", "PYTHONHOME", "VIRTUAL_ENV")


def _manim_slides_command() -> list[str]:
    """Return an executable command for *this* environment's manim-slides.

    Anchored to ``sys.executable`` first: the manim-slides we spawn must come
    from the same venv as the Simplex interpreter that's running, so a foreign
    ``manim-slides`` earlier on ``PATH`` cannot be picked up. Falls back to
    ``PATH`` and finally to ``python -m manim_slides``.
    """
    scripts_dir = Path(sys.executable).resolve().parent
    executable_name = "manim-slides.exe" if os.name == "nt" else "manim-slides"
    sibling = scripts_dir / executable_name
    if sibling.exists():
        return [str(sibling)]

    found = shutil.which("manim-slides")
    if found:
        return [found]

    return [sys.executable, "-m", "manim_slides"]


def _hermetic_env() -> dict[str, str]:
    """``os.environ`` minus interpreter-steering vars (see ``_ENV_OVERRIDE_KEYS``)."""
    return {k: v for k, v in os.environ.items() if k not in _ENV_OVERRIDE_KEYS}


def _project_root_for(deck: DeckConfig) -> Path:
    """Return the lecture-project root for a deck path."""
    resolved = deck.path.resolve()
    for parent in resolved.parents:
        if parent.name == "decks":
            return parent.parent
    return Path.cwd().resolve()


def _has_custom_config_file(args: tuple[str, ...]) -> bool:
    for index, arg in enumerate(args):
        if arg == "--config_file":
            return index + 1 < len(args)
        if arg.startswith("--config_file="):
            return True
    return False


@contextlib.contextmanager
def _merged_manim_config(
    deck: DeckConfig,
    *,
    project_root: Path,
    manim_args: tuple[str, ...],
) -> Generator[Path | None]:
    """Yield a config file path that merges project and deck Manim config."""
    if _has_custom_config_file(manim_args):
        yield None
        return

    global_cfg = project_root / "manim.cfg"
    local_cfg = deck.path / "manim.cfg"
    existing = tuple(path for path in (global_cfg, local_cfg) if path.exists())
    if not existing:
        yield None
        return
    if len(existing) == 1:
        yield existing[0]
        return

    parser = configparser.ConfigParser()
    parser.read([str(global_cfg), str(local_cfg)], encoding="utf-8")
    with tempfile.TemporaryDirectory(prefix="simplex-manim-cfg-") as tmp:
        merged = Path(tmp) / "manim.cfg"
        with merged.open("w", encoding="utf-8") as file:
            parser.write(file)
        yield merged


def render(
    deck: DeckConfig,
    *,
    output_dir: Path,
    manim_args: tuple[str, ...] = (),
    scenes: tuple[str, ...] = (),
    skip_renderers: tuple[str, ...] = (),
    write_last_frame: bool = False,
) -> None:
    """Render every scene in ``deck`` into ``output_dir`` via manim-slides.

    When ``scenes`` is non-empty, only those class names are rendered.
    When ``write_last_frame=True``, render only the first animation in each
    scene. This still constructs the full scene while keeping smoke checks fast.
    """
    groups = deck.resolve_entrypoints()
    if not groups:
        raise ValueError(f"deck {deck.slug!r} has no scenes/entrypoints configured")
    if scenes:
        groups = _filter_groups(groups, scenes)
    if skip_renderers:
        skipped = set(skip_renderers)
        groups = tuple(group for group in groups if group.renderer not in skipped)
        if not groups:
            return
    output_dir.mkdir(parents=True, exist_ok=True)
    media_dir = output_dir.resolve()
    slides_dir = media_dir / "slides"
    project_root = _project_root_for(deck)

    # Carry the deck's theme name across the subprocess via env var; the
    # manim plugin in the child interpreter reads ``SIMPLEX_THEME`` to pick
    # the preset whose background/typography it pushes onto ``manim.config``.
    env = {
        **_hermetic_env(),
        "PYTHONIOENCODING": "utf-8",
        "PYTHONUTF8": "1",
        "PYTHONWARNINGS": append_pythonwarnings_filter(os.environ.get("PYTHONWARNINGS")),
        "SIMPLEX_PROJECT_ROOT": str(project_root),
        "SIMPLEX_SLIDES_DIR": str(slides_dir.resolve()),
        "SIMPLEX_THEME": deck.theme,
    }
    if deck.slide_theme_variant is not None:
        env["SIMPLEX_THEME_VARIANT"] = deck.slide_theme_variant

    with _merged_manim_config(deck, project_root=project_root, manim_args=manim_args) as cfg:
        config_args: list[str] = ["--config_file", str(cfg)] if cfg is not None else []
        base_args: list[str] = [
            *_manim_slides_command(),
            "render",
            *config_args,
            *manim_args,
            "--media_dir",
            str(media_dir),
            "--save_sections",
        ]
        if write_last_frame:
            # ``--save_last_frame`` conflicts with ``save_sections``: Manim tries
            # to stitch section videos from image-only output. Rendering one
            # animation keeps smoke checks cheap while still exercising the scene.
            base_args.extend(["--from_animation_number", "0,0"])

        for group in groups:
            args = [
                *base_args,
            ]
            if group.renderer == "opengl":
                args.extend(["--renderer=opengl", "--write_to_movie"])
            args.extend(
                [
                    str(group.source_file.resolve()),
                    *group.scene_names,
                ]
            )
            subprocess.run(args, check=True, cwd=deck.path.resolve(), env=env)
