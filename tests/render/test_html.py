"""HTML emitter: writes slides.html with our RevealJS template + bridge."""

from pathlib import Path

from simplex.deck.config import DeckConfig
from simplex.manifest import DeckManifest, MainSlide, Subsection
from simplex.render.html import render_html
from simplex.section import SimplexSectionType


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
                section_type=SimplexSectionType.MAIN,
                subsections=(Subsection(name="Hello", section_type=SimplexSectionType.MAIN),),
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
    assert "restoreVideoPlayback" in body
    assert "finiteNumber(data.time)" in body


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
                section_type=SimplexSectionType.MAIN,
                subsections=(
                    Subsection(name="Hi", section_type=SimplexSectionType.MAIN, video=fake_video),
                ),
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
                section_type=SimplexSectionType.MAIN,
                subsections=(
                    Subsection(name="M", section_type=SimplexSectionType.MAIN),
                    Subsection(name="step2", section_type=SimplexSectionType.SUB),
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
