"""HTML emitter: writes slides.html with our RevealJS template + bridge."""

from pathlib import Path

from simplex.deck.config import DeckConfig
from simplex.render.html import render_html
from simplex.render.reconcile import DeckManifest, MainSlide, Subsection


def _deck(tmp_path: Path) -> DeckConfig:
    deck_dir = tmp_path / "demo"
    deck_dir.mkdir()
    (deck_dir / "deck.toml").write_text(
        'slug = "demo"\ntitle = "Demo"\nscenes = ["S1"]\n',
        encoding="utf-8",
    )
    (deck_dir / "slides.py").write_text("", encoding="utf-8")
    return DeckConfig.load(deck_dir)


def test_render_html_writes_slides_html(tmp_path: Path) -> None:
    deck = _deck(tmp_path)
    manifest = DeckManifest(
        deck_slug=deck.slug,
        main_slides=(
            MainSlide(
                index=1,
                scene="S1",
                name="Hello",
                section_type="simplex.main",
                subsections=(Subsection(name="Hello", type_="simplex.main"),),
            ),
        ),
    )
    out = tmp_path / "out"
    out.mkdir()
    rendered = render_html(deck, manifest, output_dir=out, static_prefix="/static")
    assert rendered.exists()
    body = rendered.read_text(encoding="utf-8")
    assert "Reveal" in body
    assert "simplex.slide" in body
    assert "tap-zone" in body
    assert "/static/reveal.js/reveal.js" in body
    assert "--simplex-bg" in body  # palette CSS injected


def test_render_html_copies_videos_when_present(tmp_path: Path) -> None:
    deck = _deck(tmp_path)
    fake_video = tmp_path / "fake.mp4"
    fake_video.write_bytes(b"\x00\x00")
    manifest = DeckManifest(
        deck_slug=deck.slug,
        main_slides=(
            MainSlide(
                index=1,
                scene="S1",
                name="Hi",
                section_type="simplex.main",
                subsections=(Subsection(name="Hi", type_="simplex.main", video=fake_video),),
            ),
        ),
    )
    out = tmp_path / "out"
    out.mkdir()
    render_html(deck, manifest, output_dir=out, static_prefix="/static")
    assert (out / "segments" / "0001_00.mp4").exists()
    html = (out / "slides.html").read_text(encoding="utf-8")
    assert "segments/0001_00.mp4" in html


def test_render_html_renders_vertical_subsections(tmp_path: Path) -> None:
    deck = _deck(tmp_path)
    manifest = DeckManifest(
        deck_slug=deck.slug,
        main_slides=(
            MainSlide(
                index=1,
                scene="S1",
                name="M",
                section_type="simplex.main",
                subsections=(
                    Subsection(name="M", type_="simplex.main"),
                    Subsection(name="step2", type_="simplex.sub"),
                ),
            ),
        ),
    )
    out = tmp_path / "out"
    out.mkdir()
    rendered = render_html(deck, manifest, output_dir=out, static_prefix="/static")
    body = rendered.read_text(encoding="utf-8")
    # Each sub gets its own <section> nested inside the main's <section>.
    assert body.count("data-sub-name=") == 2
