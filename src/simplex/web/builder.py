"""Build the full static portal under `site/`."""

from pathlib import Path

from jinja2 import Environment, PackageLoader, select_autoescape

from simplex.deck.registry import discover
from simplex.render import cache, pdf, runner
from simplex.web import notes


def _jinja() -> Environment:
    return Environment(
        loader=PackageLoader("simplex.web", "templates"),
        autoescape=select_autoescape(),
        trim_blocks=True,
        lstrip_blocks=True,
    )


def build(decks_dir: Path, site_dir: Path, cache_dir: Path) -> None:
    decks = discover(decks_dir)
    site_dir.mkdir(parents=True, exist_ok=True)
    env = _jinja()

    for deck in decks:
        out = site_dir / "decks" / deck.slug
        out.mkdir(parents=True, exist_ok=True)
        if not cache.is_fresh(deck, cache_dir):
            runner.render(deck, output_dir=out)
            pdf.export(deck, output_dir=out)
            cache.mark_fresh(deck, cache_dir)
        notes_md = deck.path / "notes.md"
        notes_html = notes.render(notes_md) if notes_md.exists() else ""
        page = env.get_template("deck.html").render(deck=deck, notes_html=notes_html)
        (out / "index.html").write_text(page, encoding="utf-8")

    index = env.get_template("index.html").render(decks=decks)
    (site_dir / "index.html").write_text(index, encoding="utf-8")
