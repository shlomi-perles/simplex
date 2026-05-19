"""Invoke ``manim-slides render`` via subprocess.

The theme/quality used to flow in via ``SIMPLEX_THEME`` / ``SIMPLEX_QUALITY``
env vars consumed by a per-scene shim in ``BaseSlide.__init__``. As of
v0.2.0 each deck declares ``plugins = simplex`` in its ``manim.cfg``; the
plugin entry-point applies theme defaults and ``save_sections = True`` at
``import manim`` time. The runner now only needs to invoke
``manim-slides render`` with the right quality flag and source file.

We still spawn a subprocess (not in-process) for three reasons: clean
SIGINT, OOM isolation, and per-deck ``manim.config`` isolation (different
decks may use different themes or qualities).

We run with ``cwd=output_dir`` so manim-slides writes its per-scene
``slides/<Scene>.json`` (PresentationConfig) to the build tree; manim's
section + video output goes to ``<output_dir>/videos/<src_stem>/<q>/...``
via ``--media_dir``.
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


def _filter_groups(
    groups: tuple[tuple[Path, tuple[str, ...]], ...],
    scenes: tuple[str, ...],
) -> tuple[tuple[Path, tuple[str, ...]], ...]:
    """Keep only entries whose class name is in ``scenes``. Drop empty groups."""
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
    write_last_frame: bool = False,
) -> None:
    """Render every scene in ``deck`` into ``output_dir`` via manim-slides.

    When ``scenes`` is non-empty, only those class names are rendered.
    When ``write_last_frame=True``, manim writes only the last frame of
    each section (used by ``simplex test`` for fast smoke checks).
    """
    groups = deck.resolve_entrypoints()
    if not groups:
        raise ValueError(f"deck {deck.slug!r} has no scenes/entrypoints configured")
    if scenes:
        groups = _filter_groups(groups, scenes)
    output_dir.mkdir(parents=True, exist_ok=True)
    media_dir = output_dir.resolve()
    quality = _quality_flag(deck.quality)

    base_args: list[str] = [
        "manim-slides",
        "render",
        "--quality",
        quality,
        "--media_dir",
        str(media_dir),
        "--save_sections",
    ]
    if not deck.caching:
        base_args.append("--disable_caching")
    if write_last_frame:
        # Manim 0.20 renamed the flag from ``--write_last_frame`` to
        # ``--save_last_frame``; both produce the same single-PNG output.
        base_args.append("--save_last_frame")

    for source_file, scene_names in groups:
        args = [
            *base_args,
            str(source_file.resolve()),
            *scene_names,
        ]
        subprocess.run(args, check=True, cwd=media_dir)
