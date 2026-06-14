"""Timeline unit loading, rebasing, validation, and fallback themes."""

from pathlib import Path

import pytest

from simplex.deck.config import DeckConfig
from simplex.manifest import SceneCue, SceneCueManifest, ThemeMedia, ThemeTimeline
from simplex.render import timeline
from simplex.render.timeline import RenderedUnit
from simplex.section import CueKind


def _deck(tmp_path: Path) -> DeckConfig:
    deck_dir = tmp_path / "demo"
    deck_dir.mkdir()
    (deck_dir / "deck.toml").write_text(
        'slug = "demo"\ntitle = "Demo"\nentrypoints = ["slides.intro:Intro"]\n',
        encoding="utf-8",
    )
    slides = deck_dir / "slides"
    slides.mkdir()
    (slides / "__init__.py").write_text("", encoding="utf-8")
    (slides / "intro.py").write_text("class Intro: ...\n", encoding="utf-8")
    return DeckConfig.load(deck_dir)


def _unit(
    scene: str,
    cue_id: str,
    *,
    frames: int = 60,
    auto_id: bool = False,
    title: str | None = None,
) -> RenderedUnit:
    cue = SceneCue(
        id=cue_id,
        kind=CueKind.SLIDE,
        title=title or cue_id.title(),
        unit=f"slides.intro:{scene}",
        start_frame=0,
        end_frame=frames,
        start=0.0,
        end=frames / 60,
        auto_id=auto_id,
    )
    return RenderedUnit(
        scene=scene,
        unit=cue.unit,
        source_file=Path("intro.py"),
        video=None,
        fps=60,
        duration=frames / 60,
        duration_frames=frames,
        cues=(cue,),
    )


def test_load_units_synthesizes_implicit_cue_without_render_output(tmp_path: Path) -> None:
    units = timeline.load_units(_deck(tmp_path), media_dir=tmp_path / "media")
    assert len(units) == 1
    assert units[0].cues[0].id == "intro"
    assert units[0].cues[0].kind is CueKind.SLIDE


def test_load_units_assigns_leading_uncued_frames_to_first_cue(tmp_path: Path) -> None:
    media_dir = tmp_path / "media"
    manifest_dir = media_dir / "simplex-cues"
    cue = SceneCue(
        id="intro",
        kind=CueKind.SLIDE,
        title="Intro",
        unit="slides.intro:Intro",
        start_frame=30,
        end_frame=60,
        start=0.5,
        end=1.0,
        auto_id=True,
    )
    SceneCueManifest(
        scene="Intro",
        unit="slides.intro:Intro",
        fps=60,
        duration=1.0,
        duration_frames=60,
        cues=(cue,),
    ).write(manifest_dir / "Intro.json")

    units = timeline.load_units(_deck(tmp_path), media_dir=media_dir)

    assert units[0].cues[0].start_frame == 0
    assert units[0].cues[0].start == 0.0
    assert units[0].cues[0].end_frame == 60


def test_rebase_cues_offsets_frames() -> None:
    cues = timeline.rebase_cues((_unit("A", "a", frames=60), _unit("B", "b", frames=120)))
    assert [(cue.id, cue.start_frame, cue.end_frame) for cue in cues] == [
        ("a", 0, 60),
        ("b", 60, 180),
    ]
    assert cues[1].start == pytest.approx(1.0)


def test_rebase_cues_renumbers_auto_ids_across_scene_units() -> None:
    cues = timeline.rebase_cues(
        (
            _unit("Intro", "hello-simplex", auto_id=True, title="Hello Simplex"),
            _unit("KeyIdea", "a-second-slide", auto_id=True, title="A Second Slide"),
        )
    )

    assert [cue.id for cue in cues] == ["hello-simplex", "a-second-slide"]


def test_rebase_cues_numbers_auto_subcues_from_main_slide_id() -> None:
    unit = _unit("Intro", "unused", auto_id=True, title="Hello Simplex")
    first = unit.cues[0]
    fragment = SceneCue(
        id="unused-fragment",
        kind=CueKind.FRAGMENT,
        title="Detail",
        unit=first.unit,
        start_frame=60,
        end_frame=120,
        start=1.0,
        end=2.0,
        auto_id=True,
    )
    loop = fragment.model_copy(
        update={
            "id": "unused-loop",
            "kind": CueKind.LOOP,
            "title": "Loop",
            "start_frame": 120,
            "end_frame": 180,
            "start": 2.0,
            "end": 3.0,
        }
    )
    cues = timeline.rebase_cues(
        (
            RenderedUnit(
                scene=unit.scene,
                unit=unit.unit,
                source_file=unit.source_file,
                video=None,
                fps=60,
                duration=3.0,
                duration_frames=180,
                cues=(first, fragment, loop),
            ),
        )
    )

    assert [cue.id for cue in cues] == ["hello-simplex", "hello-simplex-2", "hello-simplex-3"]
    assert [cue.notes_ref for cue in cues] == [
        "notes.html#hello-simplex",
        "notes.html#hello-simplex-2",
        "notes.html#hello-simplex-3",
    ]


def test_validate_theme_cues_rejects_id_drift() -> None:
    with pytest.raises(ValueError, match="cue ids do not match"):
        timeline.validate_theme_cues(
            (_unit("A", "a"),),
            (_unit("A", "different"),),
            theme_id="light",
        )


def test_css_filter_fallback_reuses_source_media() -> None:
    source = ThemeTimeline(
        id="dark",
        label="Dark",
        strategy="rendered",
        duration=2.0,
        background="#242424",
        media=ThemeMedia(hls="media/dark/hls/master.m3u8", mp4="media/dark/lecture.mp4"),
    )
    fallback = timeline.css_filter_fallback_theme(
        theme_id="light",
        label="Light",
        source=source,
        background="#eee",
    )
    assert fallback.strategy == "css_filter_fallback"
    assert fallback.source_theme == "dark"
    assert fallback.media == source.media
    assert fallback.background == "#eee"


def test_package_theme_prefers_pyav_hls_without_ffmpeg(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    videos = (tmp_path / "a.mp4", tmp_path / "b.mp4")
    for video in videos:
        video.write_bytes(b"video")
    units = tuple(
        RenderedUnit(
            scene=f"S{i}",
            unit=f"slides:S{i}",
            source_file=Path("slides.py"),
            video=video,
            fps=60,
            duration=1.0,
            duration_frames=60,
            cues=(),
        )
        for i, video in enumerate(videos)
    )
    cues = timeline.rebase_cues((_unit("S0", "s0"), _unit("S1", "s1")))

    def no_ffmpeg(_name: str) -> None:
        return None

    monkeypatch.setattr(timeline.shutil, "which", no_ffmpeg)

    def fake_write_hls_pyav(
        _lecture: Path,
        hls_dir: Path,
        *,
        segment_duration: int,
    ) -> bool:
        del segment_duration
        hls_dir.mkdir(parents=True)
        (hls_dir / "master.m3u8").write_text("#EXTM3U\n", encoding="utf-8")
        return True

    def compose_with_pyav(_videos: tuple[Path, ...], lecture: Path) -> bool:
        return lecture.write_bytes(b"lecture") > 0

    monkeypatch.setattr(timeline, "_compose_with_pyav", compose_with_pyav)
    monkeypatch.setattr(timeline, "_write_hls_pyav", fake_write_hls_pyav)

    packaged = timeline.package_theme(
        theme_id="dark",
        label="Dark",
        units=units,
        cues=cues,
        output_dir=tmp_path / "out",
        media_href_prefix="media/dark",
    )

    assert packaged.progressive_mode == "pyav"
    assert packaged.hls_available is True
    assert packaged.theme.media.hls == "media/dark/hls/master.m3u8"
    assert packaged.theme.media.mp4 == "media/dark/lecture.mp4"
    assert not any("ffmpeg is missing" in warning for warning in packaged.warnings)
