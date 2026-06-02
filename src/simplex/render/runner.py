"""Invoke ``manim-slides render`` via subprocess.

The theme/quality used to flow in via ``SIMPLEX_THEME`` / ``SIMPLEX_QUALITY``
env vars consumed by a per-scene shim in the slide base class. As of
v0.2.0 each deck declares ``plugins = simplex`` in its ``manim.cfg``; the
plugin entry-point applies theme defaults and ``save_sections = True`` at
``import manim`` time. The runner re-introduces the ``SIMPLEX_THEME`` env
var purely to *select* which preset the plugin activates -- Python's
``ContextVar`` doesn't traverse the ``subprocess`` boundary, so without
the env var every render falls back to ``SIMPLEX_DARK`` regardless of
what the deck's ``deck.toml`` declares.

We still spawn a subprocess (not in-process) for three reasons: clean
SIGINT, OOM isolation, and per-deck ``manim.config`` isolation (different
decks may use different themes or qualities).

We run with ``cwd=output_dir`` so manim-slides writes its per-scene
``slides/<Scene>.json`` (PresentationConfig) to the build tree; manim's
section + video output goes to ``<output_dir>/videos/<src_stem>/<q>/...``
via ``--media_dir``.

Quality keys (``low_quality``, ``medium_quality``, ...) come from
``manim.constants.QUALITIES`` -- the same dict Manim's own CLI reads. No
Simplex-side enum redeclares them; see :func:`_quality_flag`.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

from manim.constants import QUALITIES

from simplex.deck.config import DeckConfig, ResolvedSceneGroup
from simplex.render._warnings import append_pythonwarnings_filter


def _quality_flag(quality_key: str) -> str:
    """Look up the ``-q`` CLI letter (``l``/``m``/``h``/``p``/``k``) for a quality key.

    Reads ``manim.constants.QUALITIES`` directly so Simplex picks up any new
    preset Manim adds without a code change. ``example_quality`` has
    ``flag=None`` in Manim and isn't selectable from the CLI, so we reject it
    explicitly with the same error shape as an unknown key.
    """
    try:
        flag = QUALITIES[quality_key]["flag"]
    except KeyError:
        known = ", ".join(sorted(k for k, v in QUALITIES.items() if v["flag"] is not None))
        raise ValueError(f"unknown quality {quality_key!r}; known: {known}") from None
    if flag is None:
        known = ", ".join(sorted(k for k, v in QUALITIES.items() if v["flag"] is not None))
        raise ValueError(f"quality {quality_key!r} has no CLI flag; known: {known}")
    return flag


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


def _manim_slides_command() -> list[str]:
    """Return an executable command for the active environment's manim-slides."""
    found = shutil.which("manim-slides")
    if found:
        return [found]

    scripts_dir = Path(sys.executable).resolve().parent
    executable_name = "manim-slides.exe" if os.name == "nt" else "manim-slides"
    sibling = scripts_dir / executable_name
    if sibling.exists():
        return [str(sibling)]

    return [sys.executable, "-m", "manim_slides"]


def render(
    deck: DeckConfig,
    *,
    output_dir: Path,
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
    quality = _quality_flag(deck.quality)

    base_args: list[str] = [
        *_manim_slides_command(),
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
        # ``--save_last_frame`` conflicts with ``save_sections``: Manim tries
        # to stitch section videos from image-only output. Rendering one
        # animation keeps smoke checks cheap while still exercising the scene.
        base_args.extend(["--from_animation_number", "0,0"])

    # Carry the deck's theme name across the subprocess via env var; the
    # manim plugin in the child interpreter reads ``SIMPLEX_THEME`` to pick
    # the preset whose background/typography it pushes onto ``manim.config``.
    env = {
        **os.environ,
        "PYTHONIOENCODING": "utf-8",
        "PYTHONUTF8": "1",
        "PYTHONWARNINGS": append_pythonwarnings_filter(os.environ.get("PYTHONWARNINGS")),
        "SIMPLEX_PROJECT_ROOT": str(Path.cwd().resolve()),
        "SIMPLEX_THEME": deck.theme,
    }

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
        subprocess.run(args, check=True, cwd=media_dir, env=env)
