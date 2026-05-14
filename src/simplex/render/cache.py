"""Render cache keyed on a hash of slides.py + theme + deck.toml."""

import hashlib
import json
from pathlib import Path

from simplex.deck.config import DeckConfig


def cache_key(deck: DeckConfig) -> str:
    """Stable sha256 over inputs that affect render output."""
    parts = {
        "slides": hashlib.sha256((deck.path / "slides.py").read_bytes()).hexdigest(),
        "deck_toml": hashlib.sha256((deck.path / "deck.toml").read_bytes()).hexdigest(),
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
