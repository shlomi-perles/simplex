"""Thumbnail extraction: placeholder when no video, second-to-last sub rule."""

from pathlib import Path

from simplex.deck.config import DeckConfig
from simplex.manifest import DeckManifest, MainSlide, Subsection
from simplex.render.thumbnail import generate
from simplex.section import SimplexSectionType


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
        main_slides=(
            MainSlide(
                index=1,
                scene="S1",
                name="Intro",
                section_type=SimplexSectionType.MAIN,
                subsections=(Subsection(name="Intro", section_type=SimplexSectionType.MAIN),),
            ),
        ),
    )
    site_deck_dir = tmp_path / "site" / "decks" / "demo"
    cache_dir = tmp_path / "cache"
    site_deck_dir.mkdir(parents=True)
    out = generate(deck, manifest, site_deck_dir=site_deck_dir, cache_dir=cache_dir)
    assert 1 in out
    placeholder = site_deck_dir / out[1]
    assert placeholder.exists()
    # The placeholder must be a real, renderable image -- not the broken
    # 8-byte JPEG header we used to emit when ffmpeg was missing.
    assert placeholder.suffix == ".svg"
    body = placeholder.read_text(encoding="utf-8")
    assert body.startswith("<?xml")
    assert "<svg" in body and "</svg>" in body


def test_generate_uses_thumbnail_path_override(tmp_path: Path) -> None:
    deck_dir = tmp_path / "demo"
    deck_dir.mkdir()
    (deck_dir / "deck.toml").write_text(
        'slug = "demo"\n'
        'title = "Demo"\n'
        'scenes = ["S1"]\n'
        "\n"
        '[slides."Intro"]\n'
        'thumbnail = "hero.png"\n',
        encoding="utf-8",
    )
    (deck_dir / "slides.py").write_text("", encoding="utf-8")
    # Use a tiny 1x1 black PNG so shutil.copy2 + suffix detection works.
    hero = deck_dir / "hero.png"
    hero.write_bytes(
        bytes.fromhex(
            "89504E470D0A1A0A0000000D49484452000000010000000108060000001F15"
            "C4890000000A49444154789C6300010000000500010D0A2DB40000000049"
            "454E44AE426082"
        )
    )
    deck = DeckConfig.load(deck_dir)
    manifest = DeckManifest(
        deck_slug=deck.slug,
        main_slides=(
            MainSlide(
                index=1,
                scene="S1",
                name="Intro",
                section_type=SimplexSectionType.MAIN,
                subsections=(),
            ),
        ),
    )
    site_deck_dir = tmp_path / "site" / "decks" / "demo"
    site_deck_dir.mkdir(parents=True)
    out = generate(
        deck,
        manifest,
        site_deck_dir=site_deck_dir,
        cache_dir=tmp_path / "cache",
    )
    target = site_deck_dir / out[1]
    assert target.exists()
    assert target.name.endswith(".png")
