"""DeckConfig loading and slug validation."""

from datetime import date
from pathlib import Path

import pytest
from pydantic import ValidationError

from simplex.deck.config import DeckConfig


def _write_toml(tmp_path: Path, body: str) -> Path:
    (tmp_path / "deck.toml").write_text(body, encoding="utf-8")
    return tmp_path


def test_load_minimal(tmp_path: Path) -> None:
    deck_dir = _write_toml(tmp_path, 'slug = "demo"\ntitle = "Demo"\n')
    cfg = DeckConfig.load(deck_dir)
    assert cfg.slug == "demo"
    assert cfg.title == "Demo"
    assert cfg.theme == "simplex_dark"
    assert cfg.quality == "high_quality"


def test_invalid_slug_raises(tmp_path: Path) -> None:
    deck_dir = _write_toml(tmp_path, 'slug = "Bad_Slug"\ntitle = "x"\n')
    with pytest.raises(ValidationError):
        DeckConfig.load(deck_dir)


def test_frozen(tmp_path: Path) -> None:
    deck_dir = _write_toml(tmp_path, 'slug = "demo"\ntitle = "Demo"\n')
    cfg = DeckConfig.load(deck_dir)
    with pytest.raises(ValidationError):
        cfg.title = "other"  # type: ignore[misc]


def test_web_chrome_defaults_off(tmp_path: Path) -> None:
    """The presentation-chrome toggles default to off so legacy decks
    don't suddenly grow a clock or slide counter."""
    deck_dir = _write_toml(tmp_path, 'slug = "demo"\ntitle = "Demo"\n')
    cfg = DeckConfig.load(deck_dir)
    assert cfg.web.show_clock is False
    assert cfg.web.show_slide_number is False


def test_web_chrome_can_be_enabled(tmp_path: Path) -> None:
    deck_dir = _write_toml(
        tmp_path,
        'slug = "demo"\ntitle = "Demo"\n\n[web]\nshow_clock = true\nshow_slide_number = true\n',
    )
    cfg = DeckConfig.load(deck_dir)
    assert cfg.web.show_clock is True
    assert cfg.web.show_slide_number is True


def test_created_at_and_carousel_gif_options_load(tmp_path: Path) -> None:
    deck_dir = _write_toml(
        tmp_path,
        'slug = "demo"\n'
        'title = "Demo"\n'
        'created_at = "2026-05-19"\n'
        "\n"
        "[web]\n"
        'carousel_gif = "preview.gif"\n'
        "carousel_gif_slides = [1, 3]\n",
    )
    cfg = DeckConfig.load(deck_dir)
    assert cfg.created_at == date(2026, 5, 19)
    assert cfg.web.carousel_gif == Path("preview.gif")
    assert cfg.web.carousel_gif_slides == (1, 3)
