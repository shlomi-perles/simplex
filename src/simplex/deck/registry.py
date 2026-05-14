"""Discover decks on disk."""

from pathlib import Path

from simplex.deck.config import DeckConfig


def discover(decks_dir: Path) -> list[DeckConfig]:
    """Return every `decks/<slug>/` directory containing a `deck.toml`."""
    if not decks_dir.exists():
        return []
    found: list[DeckConfig] = []
    for entry in sorted(decks_dir.iterdir()):
        if not entry.is_dir() or entry.name.startswith("_") or entry.name.startswith("."):
            continue
        if not (entry / "deck.toml").exists():
            continue
        found.append(DeckConfig.load(entry))
    return found
