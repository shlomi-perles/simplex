"""Thumbnail extraction: placeholder when no video, second-to-last sub rule."""

from pathlib import Path

import av
import numpy as np
import pytest
from PIL import Image

from simplex.deck.config import DeckConfig
from simplex.manifest import DeckManifest, MainSlide, Subsection
from simplex.render.thumbnail import generate
from simplex.section import SimplexSectionType


def _write_solid_mp4(path: Path, color: tuple[int, int, int], frames: int = 15) -> None:
    """Write a tiny H.264 mp4 of a solid colour. Used to exercise extraction."""
    path.parent.mkdir(parents=True, exist_ok=True)
    width, height = 160, 90
    array = np.zeros((height, width, 3), dtype=np.uint8)
    array[:, :] = color
    with av.open(str(path), mode="w") as container:
        stream = container.add_stream("h264", rate=15)
        stream.width = width
        stream.height = height
        stream.pix_fmt = "yuv420p"
        for _ in range(frames):
            frame = av.VideoFrame.from_ndarray(array, format="rgb24")
            for packet in stream.encode(frame):
                container.mux(packet)
        for packet in stream.encode():
            container.mux(packet)


def _deck(tmp_path: Path) -> DeckConfig:
    deck_dir = tmp_path / "demo"
    deck_dir.mkdir()
    (deck_dir / "deck.toml").write_text(
        'slug = "demo"\ntitle = "Demo"\nscenes = ["S1"]\n', encoding="utf-8"
    )
    (deck_dir / "slides.py").write_text("", encoding="utf-8")
    return DeckConfig.load(deck_dir)


def test_generate_returns_placeholder_when_videos_absent(tmp_path: Path) -> None:
    deck = _deck(tmp_path)
    manifest = DeckManifest(
        deck_slug=deck.slug,
        main_slides=(
            MainSlide(
                index=1,
                scene="S1",
                name="Intro",
                section_type=SimplexSectionType.MAIN,
                subsections=(Subsection(name="Intro", section_type=SimplexSectionType.MAIN),),
            ),
        ),
    )
    site_deck_dir = tmp_path / "site" / "decks" / "demo"
    cache_dir = tmp_path / "cache"
    site_deck_dir.mkdir(parents=True)
    out = generate(deck, manifest, site_deck_dir=site_deck_dir, cache_dir=cache_dir)
    assert 1 in out
    placeholder = site_deck_dir / out[1]
    assert placeholder.exists()
    # The placeholder must be a real, renderable image -- not the broken
    # 8-byte JPEG header we used to emit when ffmpeg was missing.
    assert placeholder.suffix == ".svg"
    body = placeholder.read_text(encoding="utf-8")
    assert body.startswith("<?xml")
    assert "<svg" in body
    assert "</svg>" in body


def test_generate_extracts_real_frame_without_ffmpeg_cli(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Force ``ffmpeg`` off PATH and confirm the PyAV fallback delivers a real JPEG.

    This is the Windows path: manim renders via PyAV (no CLI needed), so users
    don't always have ``ffmpeg.exe`` on PATH. Before the fallback, every slide
    silently degraded to the "no preview yet" SVG.
    """
    deck = _deck(tmp_path)
    video = tmp_path / "media" / "s1.mp4"
    _write_solid_mp4(video, color=(200, 50, 50))

    manifest = DeckManifest(
        deck_slug=deck.slug,
        main_slides=(
            MainSlide(
                index=1,
                scene="S1",
                name="Intro",
                section_type=SimplexSectionType.MAIN,
                subsections=(
                    Subsection(
                        name="Intro",
                        section_type=SimplexSectionType.MAIN,
                        video=video,
                    ),
                ),
            ),
        ),
    )
    site_deck_dir = tmp_path / "site" / "decks" / "demo"
    site_deck_dir.mkdir(parents=True)

    # Force the CLI path off so the PyAV fallback is exercised.
    monkeypatch.setattr(
        "simplex.render.thumbnail.shutil.which",
        lambda _name: None,  # type: ignore[arg-type]
    )

    out = generate(deck, manifest, site_deck_dir=site_deck_dir, cache_dir=tmp_path / "cache")
    thumb = site_deck_dir / out[1]
    assert thumb.exists()
    assert thumb.suffix == ".jpg"
    with Image.open(thumb) as image:
        image.load()
        assert image.size[0] == 480  # DEFAULT_WIDTH
        # The extracted frame should be the dominant red we encoded above; we
        # check the centre pixel to tolerate the resize blur on the edges.
        center = image.getpixel((image.size[0] // 2, image.size[1] // 2))
        assert isinstance(center, tuple)
        r, g, b = center[0], center[1], center[2]
        assert r > 150
        assert g < 100
        assert b < 100


def test_generate_uses_thumbnail_path_override(tmp_path: Path) -> None:
    deck_dir = tmp_path / "demo"
    deck_dir.mkdir()
    (deck_dir / "deck.toml").write_text(
        'slug = "demo"\n'
        'title = "Demo"\n'
        'scenes = ["S1"]\n'
        "\n"
        '[slides."Intro"]\n'
        'thumbnail = "hero.png"\n',
        encoding="utf-8",
    )
    (deck_dir / "slides.py").write_text("", encoding="utf-8")
    # Use a tiny 1x1 black PNG so shutil.copy2 + suffix detection works.
    hero = deck_dir / "hero.png"
    hero.write_bytes(
        bytes.fromhex(
            "89504E470D0A1A0A0000000D49484452000000010000000108060000001F15"
            "C4890000000A49444154789C6300010000000500010D0A2DB40000000049"
            "454E44AE426082"
        )
    )
    deck = DeckConfig.load(deck_dir)
    manifest = DeckManifest(
        deck_slug=deck.slug,
        main_slides=(
            MainSlide(
                index=1,
                scene="S1",
                name="Intro",
                section_type=SimplexSectionType.MAIN,
                subsections=(),
            ),
        ),
    )
    site_deck_dir = tmp_path / "site" / "decks" / "demo"
    site_deck_dir.mkdir(parents=True)
    out = generate(
        deck,
        manifest,
        site_deck_dir=site_deck_dir,
        cache_dir=tmp_path / "cache",
    )
    target = site_deck_dir / out[1]
    assert target.exists()
    assert target.name.endswith(".png")
