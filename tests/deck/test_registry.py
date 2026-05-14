"""Sectioned discovery: featured + named sections, skip rules, deep-nest reject."""

from pathlib import Path

import pytest

from simplex.deck.registry import discover
from simplex.deck.section import FEATURED_SLUG


def _make_deck(directory: Path, slug: str) -> None:
    directory.mkdir(parents=True)
    (directory / "deck.toml").write_text(f'slug = "{slug}"\ntitle = "{slug}"\n', encoding="utf-8")
    (directory / "slides.py").write_text("", encoding="utf-8")


def _make_section(directory: Path, title: str, order: int = 100) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "_section.toml").write_text(
        f'title = "{title}"\norder = {order}\n', encoding="utf-8"
    )


def test_discover_skips_underscored_and_dotfiled(tmp_path: Path) -> None:
    _make_deck(tmp_path / "alpha", "alpha")
    _make_deck(tmp_path / "_template", "template")
    _make_deck(tmp_path / ".hidden", "hidden")
    _make_deck(tmp_path / "beta", "beta")
    registry = discover(tmp_path)
    slugs = [d.slug for d in registry.all_decks]
    assert slugs == ["alpha", "beta"]


def test_discover_missing_dir_returns_empty(tmp_path: Path) -> None:
    registry = discover(tmp_path / "nope")
    assert registry.sections == ()


def test_discover_splits_featured_from_sections(tmp_path: Path) -> None:
    _make_deck(tmp_path / "loose-deck", "loose-deck")
    _make_section(tmp_path / "graphs", "Graphs", order=10)
    _make_deck(tmp_path / "graphs" / "bfs", "bfs")
    _make_deck(tmp_path / "graphs" / "dfs", "dfs")
    registry = discover(tmp_path)
    titles = [s.config.title for s in registry.sections]
    assert "Featured" in titles
    assert "Graphs" in titles
    featured = next(s for s in registry.sections if s.config.slug == FEATURED_SLUG)
    assert [d.slug for d in featured.decks] == ["loose-deck"]


def test_default_section_order_overrides_natural_sort(tmp_path: Path) -> None:
    _make_section(tmp_path / "a", "A-sec", order=99)
    _make_deck(tmp_path / "a" / "one", "one")
    _make_section(tmp_path / "b", "B-sec", order=1)
    _make_deck(tmp_path / "b" / "two", "two")
    registry = discover(tmp_path, default_section_order=("a", "b"))
    slugs = [s.config.slug for s in registry.sections]
    assert slugs == ["a", "b"]


def test_deep_nesting_rejected(tmp_path: Path) -> None:
    nested = tmp_path / "graphs" / "subdir" / "deck"
    _make_deck(nested, "deck")
    _make_section(tmp_path / "graphs", "Graphs")
    with pytest.raises(ValueError, match="one level of sections"):
        discover(tmp_path)


def test_section_without_metadata_uses_dir_name(tmp_path: Path) -> None:
    section_dir = tmp_path / "math-foundations"
    section_dir.mkdir()
    _make_deck(section_dir / "intro", "intro")
    registry = discover(tmp_path)
    section_titles = [s.config.title for s in registry.sections]
    assert "Math Foundations" in section_titles
