"""Stable generated asset filenames for deck exports."""

from __future__ import annotations

import re

from simplex.deck.config import DeckConfig

_UNSAFE = re.compile(r'[<>:"/\\|?*\x00-\x1f]+')
_SPACE = re.compile(r"\s+")


def pdf_name(deck: DeckConfig, kind: str) -> str:
    """Return ``<deck title>-<kind>.pdf`` with filesystem-hostile chars removed."""
    title = _UNSAFE.sub("-", deck.title).strip(" .-") or deck.slug
    title = _SPACE.sub(" ", title)
    return f"{title}-{kind}.pdf"
