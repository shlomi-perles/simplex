"""`simplex new` scaffolds a deck that round-trips through `DeckConfig.load`.

The template ships with the simplex package, so the only setup the tests need
is to chdir into a fresh project directory before invoking the CLI.
"""

from pathlib import Path

import pytest
from typer.testing import CliRunner

from simplex.cli.commands import app
from simplex.deck.config import DeckConfig


@pytest.fixture
def project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    proj = tmp_path / "project"
    (proj / "decks").mkdir(parents=True)
    monkeypatch.chdir(proj)
    return proj


def test_new_creates_loadable_featured_deck(project: Path) -> None:
    result = CliRunner().invoke(app, ["new", "demo"])
    assert result.exit_code == 0, result.stdout
    deck_dir = project / "decks" / "demo"
    assert deck_dir.is_dir()
    cfg = DeckConfig.load(deck_dir)
    assert cfg.slug == "demo"
    assert (deck_dir / "slides" / "__init__.py").exists()


def test_new_section_slug_creates_nested_deck(project: Path) -> None:
    result = CliRunner().invoke(app, ["new", "graphs/bfs"])
    assert result.exit_code == 0, result.stdout
    deck_dir = project / "decks" / "graphs" / "bfs"
    assert deck_dir.is_dir()
    cfg = DeckConfig.load(deck_dir, section_slug="graphs")
    assert cfg.slug == "bfs"
