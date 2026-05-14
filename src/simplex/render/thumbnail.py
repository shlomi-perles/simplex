"""Extract per-slide JPG thumbnails from manim-slides video segments via ffmpeg.

Thumbnails are content-addressable: file name = sha256(source path + mtime + slug)
so re-rendering a slide invalidates the cached thumbnail naturally and the
generated file path stays cacheable in the browser forever.
"""

import contextlib
import hashlib
import shutil
import subprocess
from pathlib import Path

from simplex.deck.config import DeckConfig
from simplex.render.manifest import DeckManifest, SlideRef

DEFAULT_WIDTH = 480
DEFAULT_SECONDARY_WIDTH = 960
PLACEHOLDER_NAME = "_placeholder.jpg"


def _key(video: Path, slug: str) -> str:
    stat = video.stat()
    raw = f"{slug}:{video.as_posix()}:{stat.st_mtime_ns}:{stat.st_size}"
    return hashlib.sha256(raw.encode()).hexdigest()[:24]


def _run_ffmpeg(video: Path, dest: Path, width: int) -> bool:
    if shutil.which("ffmpeg") is None:
        return False
    dest.parent.mkdir(parents=True, exist_ok=True)
    args = [
        "ffmpeg",
        "-y",
        "-loglevel",
        "error",
        "-ss",
        "0.1",
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


def _placeholder(dest_dir: Path) -> Path:
    """Write a 16:9 dark JPEG placeholder once per deck and return its path."""
    placeholder = dest_dir / PLACEHOLDER_NAME
    if placeholder.exists():
        return placeholder
    placeholder.parent.mkdir(parents=True, exist_ok=True)
    if shutil.which("ffmpeg") is not None:
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-loglevel",
                "error",
                "-f",
                "lavfi",
                "-i",
                f"color=c=#242424:s={DEFAULT_WIDTH}x270:d=0.1",
                "-vframes",
                "1",
                str(placeholder),
            ],
            check=False,
            timeout=15,
        )
    if not placeholder.exists():
        # Last-resort 8-byte JPEG header; browsers will render alt text.
        placeholder.write_bytes(b"\xff\xd8\xff\xe0\x00\x00\xff\xd9")
    return placeholder


def generate(
    deck: DeckConfig,
    manifest: DeckManifest,
    *,
    site_deck_dir: Path,
    cache_dir: Path,
) -> dict[int, Path]:
    """Generate (and cache) one JPG per slide. Returns {slide.index: path}.

    Thumbnails are written into ``site_deck_dir/thumbs/`` so they live next
    to the deck's HTML. The cache key is the source video's hash; if the
    cache already has the JPG we copy from it rather than re-running ffmpeg.
    """
    thumbs_dir = site_deck_dir / "thumbs"
    cache_root = cache_dir / "thumbnails" / deck.slug
    thumbs_dir.mkdir(parents=True, exist_ok=True)
    cache_root.mkdir(parents=True, exist_ok=True)
    out: dict[int, Path] = {}
    for slide in manifest.slides:
        out[slide.index] = _one(slide, deck, thumbs_dir, cache_root)
    return out


def _one(
    slide: SlideRef,
    deck: DeckConfig,
    thumbs_dir: Path,
    cache_root: Path,
) -> Path:
    if not slide.video_paths:
        return _placeholder(thumbs_dir).relative_to(thumbs_dir.parent)
    video = slide.video_paths[0]
    if not video.exists():
        return _placeholder(thumbs_dir).relative_to(thumbs_dir.parent)
    key = _key(video, deck.slug)
    cached = cache_root / f"{key}.jpg"
    dest = thumbs_dir / f"{key}.jpg"
    if cached.exists():
        if not dest.exists():
            shutil.copy2(cached, dest)
        return dest.relative_to(thumbs_dir.parent)
    if _run_ffmpeg(video, dest, width=DEFAULT_WIDTH):
        shutil.copy2(dest, cached)
        # Generate a 2x variant for srcset.
        dest_2x = thumbs_dir / f"{key}@2x.jpg"
        _run_ffmpeg(video, dest_2x, width=DEFAULT_SECONDARY_WIDTH)
        if dest_2x.exists():
            shutil.copy2(dest_2x, cache_root / f"{key}@2x.jpg")
        return dest.relative_to(thumbs_dir.parent)
    return _placeholder(thumbs_dir).relative_to(thumbs_dir.parent)


def regenerate(
    deck: DeckConfig,
    *,
    media_dir: Path,
    cache_dir: Path,
) -> dict[int, Path]:
    """Convenience: build manifest + run `generate` in one shot for the CLI."""
    from simplex.render.manifest import build_manifest

    manifest = build_manifest(deck, media_dir=media_dir)
    return generate(deck, manifest, site_deck_dir=media_dir, cache_dir=cache_dir)
