"""Scene entrypoints for this deck.

Re-exports every scene class referenced from ``deck.toml`` so authors can
register scenes from many files behind one stable module path.
"""

from slides.intro import Intro

__all__ = ["Intro"]
