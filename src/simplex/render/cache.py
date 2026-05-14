"""Render cache keyed on a hash of source files + theme + deck.toml."""

import hashlib
import json
from pathlib import Path

from simplex.deck.config import DeckConfig

_SOURCE_GLOBS: tuple[str, ...] = ("slides.py", "slides/**/*.py", "deck.toml")


def _hash_sources(deck: DeckConfig) -> str:
    """Stable hash of every Python source file that affects render output."""
    h = hashlib.sha256()
    seen: set[Path] = set()
    for pattern in _SOURCE_GLOBS:
        for source in sorted(deck.path.glob(pattern)):
            if source in seen or not source.is_file():
                continue
            seen.add(source)
            rel = source.relative_to(deck.path).as_posix()
            h.update(rel.encode())
            h.update(b"\x00")
            h.update(source.read_bytes())
            h.update(b"\x00")
    return h.hexdigest()


def cache_key(deck: DeckConfig) -> str:
    """Stable sha256 over inputs that affect render output."""
    parts = {
        "sources": _hash_sources(deck),
        "theme": deck.theme,
        "quality": deck.quality,
    }
    return hashlib.sha256(json.dumps(parts, sort_keys=True).encode()).hexdigest()


def _stamp(deck: DeckConfig, cache_dir: Path) -> Path:
    return cache_dir / f"{deck.slug}.{cache_key(deck)}.stamp"


def is_fresh(deck: DeckConfig, cache_dir: Path) -> bool:
    return _stamp(deck, cache_dir).exists()


def mark_fresh(deck: DeckConfig, cache_dir: Path) -> None:
    cache_dir.mkdir(parents=True, exist_ok=True)
    _stamp(deck, cache_dir).touch()
