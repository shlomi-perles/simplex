"""`simplex new` scaffolds a deck that round-trips through `DeckConfig.load`."""

import shutil
from pathlib import Path

import pytest
from typer.testing import CliRunner

from simplex.cli.commands import app
from simplex.deck.config import DeckConfig


@pytest.fixture
def project_with_template(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    project = tmp_path / "project"
    decks = project / "decks"
    decks.mkdir(parents=True)
    repo_template = Path(__file__).resolve().parents[2] / "decks" / "_template"
    shutil.copytree(repo_template, decks / "_template")
    monkeypatch.chdir(project)
    return project


def test_new_creates_loadable_featured_deck(project_with_template: Path) -> None:
    result = CliRunner().invoke(app, ["new", "demo"])
    assert result.exit_code == 0, result.stdout
    deck_dir = project_with_template / "decks" / "demo"
    assert deck_dir.is_dir()
    cfg = DeckConfig.load(deck_dir)
    assert cfg.slug == "demo"
    assert (deck_dir / "slides" / "__init__.py").exists()


def test_new_section_slug_creates_nested_deck(project_with_template: Path) -> None:
    result = CliRunner().invoke(app, ["new", "graphs/bfs"])
    assert result.exit_code == 0, result.stdout
    deck_dir = project_with_template / "decks" / "graphs" / "bfs"
    assert deck_dir.is_dir()
    cfg = DeckConfig.load(deck_dir, section_slug="graphs")
    assert cfg.slug == "bfs"
