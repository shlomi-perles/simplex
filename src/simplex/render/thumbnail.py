"""Per-main-slide JPG thumbnails from the reconciled subsection MP4s.

Default rule: extract the **last frame** of the **second-to-last subsection**
(``subsections[-2]``). Configurable per main via
``deck.slides["Main Name"].thumbnail_section_index``. A literal path
override at ``deck.slides["Main Name"].thumbnail`` (relative to the deck
directory) wins over the extraction rule.

Content-addressable cache: file name = sha256 of source path + mtime + deck
slug, so re-rendering a subsection naturally invalidates its thumbnail.

The "no video" fallback ships an inline SVG so the placeholder is always
a valid image, even on systems where ffmpeg isn't installed. Production
thumbnails still use ffmpeg to extract a real frame.
"""

import contextlib
import hashlib
import shutil
import subprocess
from pathlib import Path

from simplex.deck.config import DeckConfig
from simplex.manifest import DeckManifest, MainSlide, Subsection

DEFAULT_WIDTH = 480
DEFAULT_SECONDARY_WIDTH = 960
PLACEHOLDER_NAME = "_placeholder.svg"


def _key(video: Path, slug: str) -> str:
    stat = video.stat()
    raw = f"{slug}:{video.as_posix()}:{stat.st_mtime_ns}:{stat.st_size}"
    return hashlib.sha256(raw.encode()).hexdigest()[:24]


def _run_ffmpeg(
    video: Path,
    dest: Path,
    *,
    width: int,
    seek_from_end: bool = True,
) -> bool:
    """Extract one frame near the end (or start) of `video` to `dest`.

    ``seek_from_end=True`` uses ``-sseof -0.1`` to grab the last frame --
    the right choice for a thumbnail that should represent the final
    visual state of a slide. ``False`` falls back to the very first frame
    (used by the empty-placeholder fallback).
    """
    if shutil.which("ffmpeg") is None:
        return False
    dest.parent.mkdir(parents=True, exist_ok=True)
    seek = ["-sseof", "-0.1"] if seek_from_end else ["-ss", "0.1"]
    args = [
        "ffmpeg",
        "-y",
        "-loglevel",
        "error",
        *seek,
        "-i",
        str(video),
        "-vframes",
        "1",
        "-vf",
        f"scale={width}:-2",
        "-q:v",
        "2",
        str(dest),
    ]
    with contextlib.suppress(subprocess.SubprocessError, FileNotFoundError):
        subprocess.run(args, check=True, timeout=30)
        return dest.exists()
    return False


_PLACEHOLDER_SVG = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 480 270" '
    'preserveAspectRatio="xMidYMid slice" role="img" '
    'aria-label="No preview available">'
    '<rect width="480" height="270" fill="#242424"/>'
    '<text x="240" y="142" text-anchor="middle" fill="#8a8a8a" '
    'font-family="system-ui, sans-serif" font-size="18">no preview yet</text>'
    "</svg>"
)


def _placeholder(dest_dir: Path) -> Path:
    """Write a 16:9 SVG placeholder once per deck and return its path.

    SVG works without ffmpeg and is a single inline string, so the file is
    always a valid image regardless of the host's video-tool availability.
    """
    placeholder = dest_dir / PLACEHOLDER_NAME
    if placeholder.exists():
        return placeholder
    placeholder.parent.mkdir(parents=True, exist_ok=True)
    placeholder.write_text(_PLACEHOLDER_SVG, encoding="utf-8")
    return placeholder


def _pick_source(main: MainSlide, override_idx: int) -> Subsection | None:
    """Pick which subsection's last frame to use for `main`'s thumbnail.

    Default index is ``-2`` (second-to-last); for short mains the rule
    clamps to whatever subsection exists. Returns ``None`` when the main
    has no playable subsections.
    """
    subs = main.subsections
    if not subs:
        return None
    try:
        return subs[override_idx]
    except IndexError:
        # Out-of-range index -- fall back to last available subsection.
        return subs[-1]


def generate(
    deck: DeckConfig,
    manifest: DeckManifest,
    *,
    site_deck_dir: Path,
    cache_dir: Path,
) -> dict[int, Path]:
    """Generate one JPG per main slide. Returns ``{main.index: rel_path}``."""
    thumbs_dir = site_deck_dir / "thumbs"
    cache_root = cache_dir / "thumbnails" / deck.slug
    thumbs_dir.mkdir(parents=True, exist_ok=True)
    cache_root.mkdir(parents=True, exist_ok=True)
    out: dict[int, Path] = {}
    for main in manifest.main_slides:
        out[main.index] = _one(main, deck, thumbs_dir, cache_root)
    return out


def _one(
    main: MainSlide,
    deck: DeckConfig,
    thumbs_dir: Path,
    cache_root: Path,
) -> Path:
    # Literal path override?
    override = deck.slides.get(main.name)
    if override is not None and override.thumbnail is not None:
        src = deck.path / override.thumbnail
        if src.exists():
            target = thumbs_dir / f"override_{main.index:04d}{src.suffix}"
            shutil.copy2(src, target)
            return target.relative_to(thumbs_dir.parent)

    section_index = override.thumbnail_section_index if override is not None else -2
    sub = _pick_source(main, section_index)
    if sub is None or sub.video is None or not sub.video.exists():
        return _placeholder(thumbs_dir).relative_to(thumbs_dir.parent)

    key = _key(sub.video, deck.slug)
    cached = cache_root / f"{key}.jpg"
    dest = thumbs_dir / f"{key}.jpg"
    if cached.exists():
        if not dest.exists():
            shutil.copy2(cached, dest)
        return dest.relative_to(thumbs_dir.parent)
    if _run_ffmpeg(sub.video, dest, width=DEFAULT_WIDTH, seek_from_end=True):
        shutil.copy2(dest, cached)
        dest_2x = thumbs_dir / f"{key}@2x.jpg"
        if _run_ffmpeg(sub.video, dest_2x, width=DEFAULT_SECONDARY_WIDTH, seek_from_end=True):
            shutil.copy2(dest_2x, cache_root / f"{key}@2x.jpg")
        return dest.relative_to(thumbs_dir.parent)
    return _placeholder(thumbs_dir).relative_to(thumbs_dir.parent)
