"""Cue poster and thumbnail extraction."""

from pathlib import Path

import av
import numpy as np
import pytest
from PIL import Image, ImageSequence

from simplex.deck.config import DeckConfig
from simplex.manifest import Cue
from simplex.render import thumbnail
from simplex.section import CueKind


def _write_solid_mp4(path: Path, color: tuple[int, int, int], frames: int = 15) -> None:
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


def _deck(tmp_path: Path, extra: str = "") -> DeckConfig:
    deck_dir = tmp_path / "demo"
    deck_dir.mkdir()
    (deck_dir / "deck.toml").write_text(
        'slug = "demo"\ntitle = "Demo"\nscenes = ["S1"]\n' + extra,
        encoding="utf-8",
    )
    (deck_dir / "slides.py").write_text("", encoding="utf-8")
    return DeckConfig.load(deck_dir)


def _cue() -> Cue:
    return Cue(
        id="intro",
        ordinal=1,
        kind=CueKind.SLIDE,
        title="Intro",
        unit="slides:S1",
        start_frame=0,
        end_frame=60,
        start=0.0,
        end=1.0,
    )


def test_generate_cue_images_returns_placeholders_when_video_absent(tmp_path: Path) -> None:
    deck = _deck(tmp_path)
    site_deck_dir = tmp_path / "site" / "decks" / "demo"
    images = thumbnail.generate_cue_images(
        deck,
        (_cue(),),
        theme_id="dark",
        lecture_mp4=None,
        site_deck_dir=site_deck_dir,
        cache_dir=tmp_path / "cache",
        thumbnails=True,
    )
    assert (site_deck_dir / images.thumbnails["intro"]).suffix == ".svg"
    assert (site_deck_dir / images.posters["intro"]).exists()


def test_generate_cue_images_extracts_jpegs_without_ffmpeg(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    deck = _deck(tmp_path)
    video = tmp_path / "lecture.mp4"
    _write_solid_mp4(video, (200, 50, 50))

    def no_ffmpeg(_name: str) -> None:
        return None

    monkeypatch.setattr("simplex.render.thumbnail.shutil.which", no_ffmpeg)
    site_deck_dir = tmp_path / "site" / "decks" / "demo"

    images = thumbnail.generate_cue_images(
        deck,
        (_cue(),),
        theme_id="dark",
        lecture_mp4=video,
        site_deck_dir=site_deck_dir,
        cache_dir=tmp_path / "cache",
        thumbnails=True,
    )

    thumb = site_deck_dir / images.thumbnails["intro"]
    poster = site_deck_dir / images.posters["intro"]
    assert thumb.suffix == ".jpg"
    assert poster.suffix == ".jpg"
    with Image.open(thumb) as image:
        image.load()
        assert image.size[0] == 480


def test_generate_carousel_gif_from_selected_cue(tmp_path: Path) -> None:
    deck = _deck(tmp_path, "\n[web]\ncarousel_gif_slides = [1]\n")
    video = tmp_path / "lecture.mp4"
    _write_solid_mp4(video, (30, 120, 200), frames=20)
    site_deck_dir = tmp_path / "site" / "decks" / "demo"

    rel = thumbnail.generate_carousel_gif(
        deck,
        (_cue(),),
        lecture_mp4=video,
        site_deck_dir=site_deck_dir,
        cache_dir=tmp_path / "cache",
    )

    assert rel is not None
    gif = site_deck_dir / rel
    with Image.open(gif) as image:
        image.load()
        assert image.size[0] == 320
        assert sum(1 for _ in ImageSequence.Iterator(image)) >= 1
