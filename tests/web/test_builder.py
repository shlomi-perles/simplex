"""`build(render=False)` produces index + per-deck HTML without invoking Manim."""

from pathlib import Path

from simplex.web.builder import build


def _write_deck(root: Path, slug: str, title: str) -> None:
    d = root / slug
    d.mkdir(parents=True, exist_ok=True)
    (d / "deck.toml").write_text(
        f'slug = "{slug}"\ntitle = "{title}"\nsummary = "tagline"\n',
        encoding="utf-8",
    )
    (d / "slides.py").write_text("# empty\n", encoding="utf-8")
    (d / "notes.md").write_text("# Notes\n\nMath: $a+b$.\n", encoding="utf-8")


def test_build_without_render_writes_index_and_per_deck_pages(tmp_path: Path) -> None:
    decks_dir = tmp_path / "decks"
    decks_dir.mkdir()
    _write_deck(decks_dir, "alpha", "Alpha")
    _write_deck(decks_dir, "bravo", "Bravo")

    site_dir = tmp_path / "site"
    cache_dir = tmp_path / "cache"

    build(decks_dir=decks_dir, site_dir=site_dir, cache_dir=cache_dir, render=False)

    index_html = (site_dir / "index.html").read_text(encoding="utf-8")
    assert "Alpha" in index_html
    assert "Bravo" in index_html

    alpha_html = (site_dir / "decks" / "alpha" / "index.html").read_text(encoding="utf-8")
    assert "Alpha" in alpha_html
    assert 'class="math inline"' in alpha_html
