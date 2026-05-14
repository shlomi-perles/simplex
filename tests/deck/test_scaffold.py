"""Scaffold copies _template and substitutes the slug + section tokens."""

from pathlib import Path

import pytest

from simplex.deck.config import DeckConfig
from simplex.deck.scaffold import scaffold, split_target


def _make_template(decks_dir: Path) -> None:
    template = decks_dir / "_template"
    (template / "slides").mkdir(parents=True)
    (template / "deck.toml").write_text(
        'slug = "__SLUG__"\ntitle = "__TITLE__"\nentrypoints = ["slides.intro:Intro"]\n',
        encoding="utf-8",
    )
    (template / "slides" / "__init__.py").write_text("", encoding="utf-8")
    (template / "slides" / "intro.py").write_text("class Intro: pass\n", encoding="utf-8")
    (template / "notes.md").write_text("# Notes\n", encoding="utf-8")


def test_split_target_featured() -> None:
    assert split_target("my-deck") == ("featured", "my-deck")


def test_split_target_section() -> None:
    assert split_target("graphs/bfs") == ("graphs", "bfs")


def test_split_target_rejects_extra_segments() -> None:
    with pytest.raises(ValueError, match="section/slug"):
        split_target("graphs/sub/bfs")


def test_scaffold_substitutes_slug_featured(tmp_path: Path) -> None:
    _make_template(tmp_path)
    dest = scaffold("my-deck", tmp_path)
    cfg = DeckConfig.load(dest)
    assert cfg.slug == "my-deck"
    assert cfg.title == "My Deck"
    assert dest == tmp_path / "my-deck"


def test_scaffold_sectioned_creates_section_dir(tmp_path: Path) -> None:
    _make_template(tmp_path)
    dest = scaffold("graphs/bfs", tmp_path)
    cfg = DeckConfig.load(dest, section_slug="graphs")
    assert cfg.slug == "bfs"
    assert dest == tmp_path / "graphs" / "bfs"
    assert (dest / "slides" / "__init__.py").exists()


def test_scaffold_refuses_existing(tmp_path: Path) -> None:
    _make_template(tmp_path)
    scaffold("my-deck", tmp_path)
    with pytest.raises(FileExistsError):
        scaffold("my-deck", tmp_path)
