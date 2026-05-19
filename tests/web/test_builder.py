"""`build(render=False)` emits home + section + per-deck HTML without manim."""

from pathlib import Path

from simplex.web.builder import build
from simplex.web.site_config import SiteConfig


def _write_deck(root: Path, slug: str, title: str, *, scenes: tuple[str, ...] = ()) -> None:
    d = root / slug
    d.mkdir(parents=True, exist_ok=True)
    scenes_line = ""
    if scenes:
        joined = ", ".join(f'"{s}"' for s in scenes)
        scenes_line = f"scenes = [{joined}]\n"
    (d / "deck.toml").write_text(
        f'slug = "{slug}"\ntitle = "{title}"\nsummary = "tagline"\n{scenes_line}',
        encoding="utf-8",
    )
    (d / "slides.py").write_text("# empty\n", encoding="utf-8")
    (d / "notes.md").write_text("# Notes\n\nMath: $a+b$. See [slide:1].\n", encoding="utf-8")


def _write_section(root: Path, name: str, title: str, order: int) -> None:
    section = root / name
    section.mkdir(parents=True, exist_ok=True)
    (section / "_section.toml").write_text(
        f'title = "{title}"\norder = {order}\n', encoding="utf-8"
    )


def test_build_emits_home_and_per_deck_pages(tmp_path: Path) -> None:
    decks_dir = tmp_path / "decks"
    decks_dir.mkdir()
    _write_deck(decks_dir, "alpha", "Alpha", scenes=("S1",))
    _write_deck(decks_dir, "bravo", "Bravo", scenes=("S1",))

    site_dir = tmp_path / "site"

    build(
        decks_dir=decks_dir,
        site_dir=site_dir,
        render=False,
        site_cfg=SiteConfig(brand="Simplex"),
    )

    index_html = (site_dir / "index.html").read_text(encoding="utf-8")
    assert "Alpha" in index_html
    assert "Bravo" in index_html
    assert "carousel" in index_html
    # Palette CSS injected into <head>.
    assert "--simplex-bg" in index_html
    # Site CSS loads after palette tokens so deck palettes cannot override body chrome.
    assert index_html.index("--simplex-bg") < index_html.index("simplex.css")

    alpha_html = (site_dir / "decks" / "alpha" / "index.html").read_text(encoding="utf-8")
    assert "Alpha" in alpha_html
    assert 'class="math inline"' in alpha_html
    assert 'class="slide-ref"' in alpha_html
    slides_html = (site_dir / "decks" / "alpha" / "slides.html").read_text(encoding="utf-8")
    assert "Reveal" in slides_html
    assert "--simplex-bg" in slides_html


def test_build_emits_section_pages_and_orders(tmp_path: Path) -> None:
    decks_dir = tmp_path / "decks"
    decks_dir.mkdir()
    _write_section(decks_dir, "graphs", "Graphs", order=1)
    _write_deck(decks_dir / "graphs", "bfs", "BFS", scenes=("S1",))
    _write_deck(decks_dir, "intro", "Featured Intro", scenes=("S1",))

    site_dir = tmp_path / "site"

    build(
        decks_dir=decks_dir,
        site_dir=site_dir,
        render=False,
        site_cfg=SiteConfig(brand="Simplex"),
    )

    home = (site_dir / "index.html").read_text(encoding="utf-8")
    assert "Graphs" in home
    assert "Featured" in home

    section_page = (site_dir / "sections" / "graphs" / "index.html").read_text(encoding="utf-8")
    assert "BFS" in section_page

    featured_page = (site_dir / "sections" / "featured" / "index.html").read_text(encoding="utf-8")
    assert "Featured Intro" in featured_page


def test_build_gates_ga_tag(tmp_path: Path) -> None:
    decks_dir = tmp_path / "decks"
    decks_dir.mkdir()
    _write_deck(decks_dir, "alpha", "Alpha", scenes=("S1",))
    site_dir = tmp_path / "site"

    build(
        decks_dir=decks_dir,
        site_dir=site_dir,
        render=False,
        site_cfg=SiteConfig(brand="Simplex"),
    )
    assert "gtag" not in (site_dir / "index.html").read_text(encoding="utf-8")

    build(
        decks_dir=decks_dir,
        site_dir=site_dir,
        render=False,
        site_cfg=SiteConfig(brand="Simplex", ga_tag="G-TEST"),
    )
    assert "G-TEST" in (site_dir / "index.html").read_text(encoding="utf-8")

    build(
        decks_dir=decks_dir,
        site_dir=site_dir,
        render=False,
        site_cfg=SiteConfig(brand="Simplex", ga_tag="G-TEST", preview=True),
    )
    assert "gtag" not in (site_dir / "index.html").read_text(encoding="utf-8")
