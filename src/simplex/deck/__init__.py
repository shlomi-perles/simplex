"""Deck configuration, discovery, and scaffolder."""

from simplex.deck.config import DeckConfig
from simplex.deck.registry import discover
from simplex.deck.scaffold import scaffold

__all__ = ["DeckConfig", "discover", "scaffold"]
