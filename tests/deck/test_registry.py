"""Deck discovery skips _underscored and .dotfiled directories."""

from pathlib import Path

from simplex.deck.registry import discover


def _make_deck(dir: Path, slug: str) -> None:
    dir.mkdir(parents=True)
    (dir / "deck.toml").write_text(f'slug = "{slug}"\ntitle = "{slug}"\n', encoding="utf-8")
    (dir / "slides.py").write_text("", encoding="utf-8")


def test_discover_skips_underscored(tmp_path: Path) -> None:
    _make_deck(tmp_path / "alpha", "alpha")
    _make_deck(tmp_path / "_template", "template")
    _make_deck(tmp_path / "beta", "beta")
    slugs = [d.slug for d in discover(tmp_path)]
    assert slugs == ["alpha", "beta"]


def test_discover_missing_dir_returns_empty(tmp_path: Path) -> None:
    assert discover(tmp_path / "does-not-exist") == []
