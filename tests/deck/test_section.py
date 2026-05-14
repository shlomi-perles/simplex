"""SectionConfig: load from `_section.toml`, fall back to humanised dir name."""

from pathlib import Path

from simplex.deck.section import FEATURED_SLUG, SectionConfig


def test_load_with_toml(tmp_path: Path) -> None:
    (tmp_path / "_section.toml").write_text(
        'title = "Graphs & Trees"\norder = 10\nblurb = "DFS/BFS"\nicon = "graph"\n',
        encoding="utf-8",
    )
    cfg = SectionConfig.load(tmp_path)
    assert cfg.title == "Graphs & Trees"
    assert cfg.order == 10
    assert cfg.blurb == "DFS/BFS"
    assert cfg.icon == "graph"
    assert cfg.slug == tmp_path.name


def test_load_without_toml_uses_dir_name(tmp_path: Path) -> None:
    section_dir = tmp_path / "math-foundations"
    section_dir.mkdir()
    cfg = SectionConfig.load(section_dir)
    assert cfg.title == "Math Foundations"
    assert cfg.slug == "math-foundations"


def test_featured_synthetic() -> None:
    cfg = SectionConfig.featured()
    assert cfg.slug == FEATURED_SLUG
    assert cfg.order == 0
