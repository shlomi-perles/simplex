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
"""

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


def render(deck: DeckConfig, *, output_dir: Path) -> None:
    """Render every scene in `deck` into `output_dir` via manim-slides."""
    groups = deck.resolve_entrypoints()
    if not groups:
        raise ValueError(f"deck {deck.slug!r} has no scenes/entrypoints configured")
    output_dir.mkdir(parents=True, exist_ok=True)
    media_dir = output_dir.resolve()
    quality = _quality_flag(deck.quality)

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
        subprocess.run(args, check=True, cwd=media_dir)
