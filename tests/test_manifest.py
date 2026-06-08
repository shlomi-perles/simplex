"""Manifest v2 schema helpers and validation."""

import pytest
from pydantic import ValidationError

from simplex.manifest import Cue, DeckInfo, DeckManifest, ThemeMedia, ThemeTimeline
from simplex.section import CueKind


def _cue(cue_id: str, ordinal: int, start_frame: int, end_frame: int) -> Cue:
    return Cue(
        id=cue_id,
        ordinal=ordinal,
        kind=CueKind.SLIDE,
        title=cue_id.title(),
        unit="slides.intro:Intro",
        start_frame=start_frame,
        end_frame=end_frame,
        start=start_frame / 60,
        end=end_frame / 60,
    )


def test_empty_manifest_is_schema_v2() -> None:
    manifest = DeckManifest.empty("demo", "Demo")
    assert manifest.schema_version == 2
    assert manifest.deck_slug == "demo"
    assert manifest.slide_count == 0


def test_manifest_counts_only_slide_cues() -> None:
    manifest = DeckManifest(
        deck=DeckInfo(slug="demo", title="Demo"),
        generated_at="2026-06-08T12:00:00+00:00",
        fps=60,
        duration=2.0,
        cues=(
            _cue("intro", 1, 0, 60),
            _cue("detail", 2, 60, 120).model_copy(update={"kind": CueKind.FRAGMENT}),
        ),
        themes=(
            ThemeTimeline(
                id="dark",
                label="Dark",
                strategy="rendered",
                duration=2.0,
                background="#242424",
                media=ThemeMedia(hls="media/dark/hls/master.m3u8", mp4="media/dark/lecture.mp4"),
            ),
        ),
    )
    assert manifest.slide_count == 1
    assert manifest.find("detail") is not None
    assert manifest.theme("dark") is not None


def test_duplicate_cue_ids_are_rejected() -> None:
    with pytest.raises(ValidationError, match="duplicate cue id"):
        DeckManifest(
            deck=DeckInfo(slug="demo", title="Demo"),
            generated_at="2026-06-08T12:00:00+00:00",
            fps=60,
            duration=2.0,
            cues=(_cue("intro", 1, 0, 60), _cue("intro", 2, 60, 120)),
        )


def test_css_filter_fallback_requires_source_theme() -> None:
    with pytest.raises(ValidationError, match="source_theme"):
        ThemeTimeline(
            id="light",
            label="Light",
            strategy="css_filter_fallback",
            media=ThemeMedia(mp4="media/dark/lecture.mp4"),
        )


def test_json_round_trip() -> None:
    manifest = DeckManifest(
        deck=DeckInfo(slug="demo", title="Demo"),
        generated_at="2026-06-08T12:00:00+00:00",
        fps=60,
        duration=1.0,
        cues=(_cue("intro", 1, 0, 60),),
        themes=(
            ThemeTimeline(
                id="dark",
                label="Dark",
                strategy="rendered",
                duration=1.0,
                background="#242424",
                media=ThemeMedia(mp4="media/dark/lecture.mp4"),
            ),
        ),
    )
    revived = DeckManifest.model_validate_json(manifest.to_public_json())
    assert revived == manifest
    assert revived.themes[0].background == "#242424"
