"""Scaffold copies _template and substitutes the slug + section tokens."""

from pathlib import Path

import pytest

from simplex.deck.config import DeckConfig
from simplex.deck.scaffold import scaffold, split_target


@pytest.fixture
def template_dir(tmp_path: Path) -> Path:
    """Build a minimal token-bearing template the scaffold can copy."""
    template = tmp_path / "_template"
    (template / "slides").mkdir(parents=True)
    (template / "deck.toml").write_text(
        'slug = "__SLUG__"\ntitle = "__TITLE__"\nentrypoints = ["slides.intro:Intro"]\n',
        encoding="utf-8",
    )
    (template / "slides" / "__init__.py").write_text("", encoding="utf-8")
    (template / "slides" / "intro.py").write_text("class Intro: pass\n", encoding="utf-8")
    (template / "notes.md").write_text("# Notes\n", encoding="utf-8")
    return template


def test_split_target_featured() -> None:
    assert split_target("my-deck") == ("featured", "my-deck")


def test_split_target_section() -> None:
    assert split_target("graphs/bfs") == ("graphs", "bfs")


def test_split_target_rejects_extra_segments() -> None:
    with pytest.raises(ValueError, match="section/slug"):
        split_target("graphs/sub/bfs")


def test_scaffold_substitutes_slug_featured(tmp_path: Path, template_dir: Path) -> None:
    decks = tmp_path / "decks"
    decks.mkdir()
    dest = scaffold("my-deck", decks, template_dir=template_dir)
    cfg = DeckConfig.load(dest)
    assert cfg.slug == "my-deck"
    assert cfg.title == "My Deck"
    assert dest == decks / "my-deck"


def test_scaffold_sectioned_creates_section_dir(tmp_path: Path, template_dir: Path) -> None:
    decks = tmp_path / "decks"
    decks.mkdir()
    dest = scaffold("graphs/bfs", decks, template_dir=template_dir)
    cfg = DeckConfig.load(dest, section_slug="graphs")
    assert cfg.slug == "bfs"
    assert dest == decks / "graphs" / "bfs"
    assert (dest / "slides" / "__init__.py").exists()


def test_scaffold_refuses_existing(tmp_path: Path, template_dir: Path) -> None:
    decks = tmp_path / "decks"
    decks.mkdir()
    scaffold("my-deck", decks, template_dir=template_dir)
    with pytest.raises(FileExistsError):
        scaffold("my-deck", decks, template_dir=template_dir)


def test_scaffold_uses_bundled_template_by_default(tmp_path: Path) -> None:
    """No template_dir -> pick up the one bundled in the simplex package."""
    decks = tmp_path / "decks"
    decks.mkdir()
    dest = scaffold("my-deck", decks)
    cfg = DeckConfig.load(dest)
    assert cfg.slug == "my-deck"
    assert (dest / "slides" / "intro.py").exists()
