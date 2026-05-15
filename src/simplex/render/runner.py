"""Invoke `manim-slides render` via subprocess.

Each `module:Class` entrypoint resolves to the file that physically defines the
class (`slides/scenes.py`, `slides/intro.py`, the legacy single-file
`slides.py`, ...). We group entrypoints by file and invoke `manim-slides render`
once per file with that file's scene classes.

Why per-file (instead of pointing at a re-exporting `slides/__init__.py`):
manim's scene discovery filters by `obj.__module__.startswith(loaded_module)`,
so a class imported into `__init__.py` from elsewhere is rejected and you get
"There are no scenes inside that module".

Why we run with `cwd=output_dir` (not the deck dir): manim-slides writes its
per-scene PresentationConfig JSON and per-slide video chunks to a `./slides/`
folder hard-coded relative to cwd. Running from `output_dir` keeps every
emitted artefact under the build tree so the manifest, thumbnail, and PDF
steps can find it -- and keeps the deck source directory untouched.

Theme propagation: deck.toml's `theme` and `quality` are passed to the child
process via `SIMPLEX_THEME` / `SIMPLEX_QUALITY` env vars. `BaseSlide.__init__`
reads them and configures Manim before `Scene.__init__` builds the camera, so
`config.background_color` reaches the camera (otherwise the camera locks in
Manim's default black and our theme palette is ignored).
"""

import os
import subprocess
from pathlib import Path

from simplex.deck.config import DeckConfig

_QUALITY_FLAGS: dict[str, str] = {
    "low_quality": "l",
    "medium_quality": "m",
    "high_quality": "h",
    "production_quality": "p",
    "fourk_quality": "k",
    "example_quality": "e",
}


def _quality_flag(quality_key: str) -> str:
    if quality_key not in _QUALITY_FLAGS:
        known = ", ".join(sorted(_QUALITY_FLAGS))
        raise ValueError(f"unknown quality {quality_key!r}; known: {known}")
    return _QUALITY_FLAGS[quality_key]


def _filter_groups(
    groups: tuple[tuple[Path, tuple[str, ...]], ...],
    scenes: tuple[str, ...],
) -> tuple[tuple[Path, tuple[str, ...]], ...]:
    """Keep only entries whose class name is in `scenes`. Drop empty groups."""
    wanted = set(scenes)
    available = {name for _, names in groups for name in names}
    unknown = wanted - available
    if unknown:
        raise ValueError(
            f"unknown scene name(s): {sorted(unknown)!r}; known: {sorted(available)!r}"
        )
    filtered: list[tuple[Path, tuple[str, ...]]] = []
    for source_file, names in groups:
        kept = tuple(n for n in names if n in wanted)
        if kept:
            filtered.append((source_file, kept))
    return tuple(filtered)


def render(
    deck: DeckConfig,
    *,
    output_dir: Path,
    scenes: tuple[str, ...] = (),
) -> None:
    """Render every scene in `deck` into `output_dir` via manim-slides.

    When `scenes` is non-empty, only those class names are rendered. Other
    scenes' previously rendered outputs are left untouched on disk.
    """
    groups = deck.resolve_entrypoints()
    if not groups:
        raise ValueError(f"deck {deck.slug!r} has no scenes/entrypoints configured")
    if scenes:
        groups = _filter_groups(groups, scenes)
    output_dir.mkdir(parents=True, exist_ok=True)
    media_dir = output_dir.resolve()
    quality = _quality_flag(deck.quality)
    env = {
        **os.environ,
        "SIMPLEX_THEME": deck.theme,
        "SIMPLEX_QUALITY": deck.quality,
    }

    for source_file, scene_names in groups:
        args: list[str] = [
            "manim-slides",
            "render",
            "--quality",
            quality,
            "--media_dir",
            str(media_dir),
            str(source_file.resolve()),
            *scene_names,
        ]
        subprocess.run(args, check=True, cwd=media_dir, env=env)
