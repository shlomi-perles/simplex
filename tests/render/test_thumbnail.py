"""Thumbnail caching: placeholder path when no video / no ffmpeg."""

from pathlib import Path

from simplex.deck.config import DeckConfig
from simplex.render.manifest import DeckManifest, SlideRef
from simplex.render.thumbnail import generate


def _deck(tmp_path: Path) -> DeckConfig:
    deck_dir = tmp_path / "demo"
    deck_dir.mkdir()
    (deck_dir / "deck.toml").write_text(
        'slug = "demo"\ntitle = "Demo"\nscenes = ["S1"]\n', encoding="utf-8"
    )
    (deck_dir / "slides.py").write_text("", encoding="utf-8")
    return DeckConfig.load(deck_dir)


def test_generate_returns_placeholder_when_videos_absent(tmp_path: Path) -> None:
    deck = _deck(tmp_path)
    manifest = DeckManifest(
        deck_slug=deck.slug,
        slides=(SlideRef(index=0, scene="S1"),),
    )
    site_deck_dir = tmp_path / "site" / "decks" / "demo"
    cache_dir = tmp_path / "cache"
    site_deck_dir.mkdir(parents=True)
    out = generate(deck, manifest, site_deck_dir=site_deck_dir, cache_dir=cache_dir)
    assert 0 in out
    # Placeholder path is relative to site_deck_dir.
    placeholder = site_deck_dir / out[0]
    assert placeholder.exists()
