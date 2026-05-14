"""Scaffold copies _template and substitutes the slug."""

from pathlib import Path

import pytest

from simplex.deck.config import DeckConfig
from simplex.deck.scaffold import scaffold


def _make_template(decks_dir: Path) -> None:
    template = decks_dir / "_template"
    template.mkdir(parents=True)
    (template / "deck.toml").write_text(
        'slug = "__SLUG__"\ntitle = "New deck"\n',
        encoding="utf-8",
    )
    (template / "slides.py").write_text("", encoding="utf-8")
    (template / "notes.md").write_text("# Notes\n", encoding="utf-8")


def test_scaffold_substitutes_slug(tmp_path: Path) -> None:
    _make_template(tmp_path)
    dest = scaffold("my-deck", tmp_path)
    cfg = DeckConfig.load(dest)
    assert cfg.slug == "my-deck"


def test_scaffold_refuses_existing(tmp_path: Path) -> None:
    _make_template(tmp_path)
    scaffold("my-deck", tmp_path)
    with pytest.raises(FileExistsError):
        scaffold("my-deck", tmp_path)
