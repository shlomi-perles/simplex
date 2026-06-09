"""Invoke Manim directly for timeline-native Simplex scene units."""

from __future__ import annotations

import configparser
import contextlib
import os
import subprocess
import sys
import tempfile
from collections.abc import Generator
from pathlib import Path

from simplex.deck.config import DeckConfig, ResolvedSceneGroup
from simplex.render._warnings import append_pythonwarnings_filter

_ENV_OVERRIDE_KEYS = ("PYTHONPATH", "PYTHONHOME", "VIRTUAL_ENV")


def _filter_groups(
    groups: tuple[ResolvedSceneGroup, ...],
    scenes: tuple[str, ...],
) -> tuple[ResolvedSceneGroup, ...]:
    wanted = set(scenes)
    available = {name for group in groups for name in group.scene_names}
    unknown = wanted - available
    if unknown:
        raise ValueError(
            f"unknown scene name(s): {sorted(unknown)!r}; known: {sorted(available)!r}"
        )
    filtered: list[ResolvedSceneGroup] = []
    for group in groups:
        kept = tuple(name for name in group.scene_names if name in wanted)
        if kept:
            filtered.append(
                ResolvedSceneGroup(
                    source_file=group.source_file,
                    scene_names=kept,
                    renderer=group.renderer,
                )
            )
    return tuple(filtered)


def _manim_command() -> list[str]:
    return [sys.executable, "-m", "manim"]


def _hermetic_env() -> dict[str, str]:
    return {k: v for k, v in os.environ.items() if k not in _ENV_OVERRIDE_KEYS}


def _project_root_for(deck: DeckConfig) -> Path:
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
    """Yield a config file that merges project and deck Manim config."""
    if _has_custom_config_file(manim_args):
        yield None
        return

    parser = configparser.ConfigParser()
    global_cfg = project_root / "manim.cfg"
    local_cfg = deck.path / "manim.cfg"
    existing = [str(path) for path in (global_cfg, local_cfg) if path.exists()]
    if existing:
        parser.read(existing, encoding="utf-8")

    if not parser.sections():
        yield None
        return

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
    """Render every scene unit in ``deck`` into an intermediate media directory."""
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
    cues_dir = media_dir / "simplex-cues"
    cues_dir.mkdir(parents=True, exist_ok=True)
    project_root = _project_root_for(deck)

    env = {
        **_hermetic_env(),
        "PYTHONIOENCODING": "utf-8",
        "PYTHONUTF8": "1",
        "PYTHONWARNINGS": append_pythonwarnings_filter(os.environ.get("PYTHONWARNINGS")),
        "SIMPLEX_PROJECT_ROOT": str(project_root),
        "SIMPLEX_CUES_DIR": str(cues_dir.resolve()),
        "SIMPLEX_THEME": deck.theme,
    }
    if deck.slide_theme_variant is not None:
        env["SIMPLEX_THEME_VARIANT"] = deck.slide_theme_variant

    with _merged_manim_config(deck, project_root=project_root, manim_args=manim_args) as cfg:
        config_args: list[str] = ["--config_file", str(cfg)] if cfg is not None else []
        base_args: list[str] = [
            *_manim_command(),
            *config_args,
            *manim_args,
        ]
        base_args.extend(["--media_dir", str(media_dir)])
        if write_last_frame:
            base_args.extend(["--from_animation_number", "0,0"])

        for group in groups:
            args = [*base_args]
            if group.renderer == "opengl":
                args.extend(["--renderer=opengl", "--write_to_movie"])
            args.extend([str(group.source_file.resolve()), *group.scene_names])
            subprocess.run(args, check=True, cwd=deck.path.resolve(), env=env)
