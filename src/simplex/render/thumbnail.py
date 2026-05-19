"""Per-main-slide JPG thumbnails from the reconciled subsection MP4s.

Default rule: extract the **last frame** of the **second-to-last subsection**
(``subsections[-2]``). Configurable per main via
``deck.slides["Main Name"].thumbnail_section_index``. A literal path
override at ``deck.slides["Main Name"].thumbnail`` (relative to the deck
directory) wins over the extraction rule.

Content-addressable cache: file name = sha256 of source path + mtime + deck
slug, so re-rendering a subsection naturally invalidates its thumbnail.

Extraction tries the system ``ffmpeg`` CLI first (fastest), then falls back
to PyAV -- manim already depends on PyAV for its own concatenation pipeline,
so this fallback works without any extra system binaries (the typical reason
real previews showed "no preview yet" on Windows: manim runs via PyAV but
ffmpeg.exe is not on PATH, so the old code went straight to the placeholder).
The "no video" fallback ships an inline SVG so the placeholder is always a
valid image even when neither extractor can run.
"""

import contextlib
import hashlib
import shutil
import subprocess
from pathlib import Path

import av
import av.error
from PIL.Image import Resampling

from simplex.deck.config import DeckConfig
from simplex.manifest import DeckManifest, MainSlide, Subsection

DEFAULT_WIDTH = 480
DEFAULT_SECONDARY_WIDTH = 960
PLACEHOLDER_NAME = "_placeholder.svg"


def _key(video: Path, slug: str) -> str:
    stat = video.stat()
    raw = f"{slug}:{video.as_posix()}:{stat.st_mtime_ns}:{stat.st_size}"
    return hashlib.sha256(raw.encode()).hexdigest()[:24]


def _extract_frame(
    video: Path,
    dest: Path,
    *,
    width: int,
    seek_from_end: bool = True,
) -> bool:
    """Extract one frame near the end (or start) of ``video`` to ``dest``.

    Tries ``ffmpeg`` first; falls back to PyAV (bundled with manim) when the
    CLI is missing. Returns ``True`` on success.
    """
    dest.parent.mkdir(parents=True, exist_ok=True)
    if _try_ffmpeg(video, dest, width=width, seek_from_end=seek_from_end):
        return True
    return _try_pyav(video, dest, width=width, seek_from_end=seek_from_end)


def _try_ffmpeg(
    video: Path,
    dest: Path,
    *,
    width: int,
    seek_from_end: bool,
) -> bool:
    """Extract a frame via the ``ffmpeg`` CLI if it's on PATH."""
    if shutil.which("ffmpeg") is None:
        return False
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


def _try_pyav(
    video: Path,
    dest: Path,
    *,
    width: int,
    seek_from_end: bool,
) -> bool:
    """Decode a representative frame with PyAV and save it as JPEG.

    Walks every frame and keeps the last when ``seek_from_end`` is true; for
    typical slide-length clips (<10 s) that's still fast and avoids the
    container-specific seek edge cases (no-keyframe, B-frame ordering, etc.)
    that bite when you try to seek directly to the tail.
    """
    try:
        with av.open(str(video)) as container:
            stream = container.streams.video[0]
            stream.thread_type = "AUTO"
            chosen = None
            for frame in container.decode(stream):
                chosen = frame
                if not seek_from_end:
                    break
            if chosen is None:
                return False
            image = chosen.to_image()
    except (av.error.FFmpegError, IndexError, OSError):
        return False
    src_w, src_h = image.size
    if src_w <= 0 or src_h <= 0:
        return False
    target_h = max(1, round(src_h * width / src_w))
    if (src_w, src_h) != (width, target_h):
        image = image.resize((width, target_h), Resampling.LANCZOS)
    image.save(str(dest), "JPEG", quality=85, optimize=True)
    return dest.exists()


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
    """Pick which subsection's frame to use for `main`'s thumbnail.

    Returns the subsection at ``override_idx`` if it has a usable video,
    otherwise walks the remaining subsections (last-to-first) so a missing
    video at ``-1`` (e.g. the trailing skip-animations section Manim emits
    when ``construct()`` ends without a final ``play()``) doesn't degrade
    into the placeholder. Returns ``None`` only when the main has no
    playable video at any index.
    """
    subs = main.subsections
    if not subs:
        return None
    try:
        primary = subs[override_idx]
    except IndexError:
        primary = subs[-1]
    if _has_video(primary):
        return primary
    # Fallback: scan from last to first, skipping the primary we already
    # tried. The last sub usually carries the slide's final visual state
    # (the most informative thumbnail), so we prefer it over earlier ones.
    for sub in reversed(subs):
        if sub is primary:
            continue
        if _has_video(sub):
            return sub
    return primary


def _has_video(sub: Subsection) -> bool:
    return sub.video is not None and sub.video.exists()


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
    if _extract_frame(sub.video, dest, width=DEFAULT_WIDTH, seek_from_end=True):
        shutil.copy2(dest, cached)
        dest_2x = thumbs_dir / f"{key}@2x.jpg"
        if _extract_frame(sub.video, dest_2x, width=DEFAULT_SECONDARY_WIDTH, seek_from_end=True):
            shutil.copy2(dest_2x, cache_root / f"{key}@2x.jpg")
        return dest.relative_to(thumbs_dir.parent)
    return _placeholder(thumbs_dir).relative_to(thumbs_dir.parent)
