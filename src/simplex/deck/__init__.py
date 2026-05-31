"""Deck configuration, discovery, and scaffolder."""

from simplex.deck.config import DeckConfig, ResolvedSlideThemes, SlideThemeConfig
from simplex.deck.registry import discover
from simplex.deck.scaffold import scaffold

__all__ = ["DeckConfig", "ResolvedSlideThemes", "SlideThemeConfig", "discover", "scaffold"]
