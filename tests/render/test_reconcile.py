"""Reconcile: group manim's native section JSON into main/sub tree."""

import json
from pathlib import Path

import pytest

from simplex.deck.config import DeckConfig
from simplex.render.reconcile import build_manifest


def _deck(tmp_path: Path) -> DeckConfig:
    deck_dir = tmp_path / "demo"
    deck_dir.mkdir()
    (deck_dir / "deck.toml").write_text(
        'slug = "demo"\ntitle = "Demo"\nscenes = ["TextHelpers", "CodeHelpers"]\n',
        encoding="utf-8",
    )
    (deck_dir / "slides.py").write_text("", encoding="utf-8")
    return DeckConfig.load(deck_dir)


def _write_sections(media_dir: Path, scene: str, rows: list[dict[str, object]]) -> Path:
    """Write a fake sections JSON at <media>/videos/foo/720p30/sections/<scene>.json."""
    sections_dir = media_dir / "videos" / "foo" / "720p30" / "sections"
    sections_dir.mkdir(parents=True, exist_ok=True)
    json_path = sections_dir / f"{scene}.json"
    json_path.write_text(json.dumps(rows), encoding="utf-8")
    return sections_dir


def test_manifest_synthetic_when_no_sections(tmp_path: Path) -> None:
    deck = _deck(tmp_path)
    media_dir = tmp_path / "media"
    media_dir.mkdir()
    manifest = build_manifest(deck, media_dir=media_dir)
    assert manifest.slide_count == 2
    assert [m.scene for m in manifest.main_slides] == ["TextHelpers", "CodeHelpers"]


def test_manifest_uses_presentation_videos_when_sections_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    deck = _deck(tmp_path)
    media_dir = tmp_path / "media"
    files_dir = media_dir / "slides" / "files" / "TextHelpers"
    files_dir.mkdir(parents=True)
    (files_dir / "a.mp4").write_bytes(b"fake")
    (files_dir / "b.mp4").write_bytes(b"fake")
    slides_dir = media_dir / "slides"
    (slides_dir / "TextHelpers.json").write_text(
        json.dumps(
            {
                "slides": [
                    {"type": "video", "file": "slides\\files\\TextHelpers\\a.mp4"},
                    {"type": "video", "file": "slides\\files\\TextHelpers\\b.mp4"},
                ]
            }
        ),
        encoding="utf-8",
    )

    def fake_duration(video: Path) -> float:
        return {"a.mp4": 1.25, "b.mp4": 2.75}[video.name]

    monkeypatch.setattr("simplex.render.reconcile._media_duration", fake_duration)

    manifest = build_manifest(deck, media_dir=media_dir)
    text = manifest.main_slides[0]

    assert text.duration_s == 4.0
    assert [sub.duration_s for sub in text.subsections] == [1.25, 2.75]


def test_manifest_groups_subs_under_main(tmp_path: Path) -> None:
    deck = _deck(tmp_path)
    media_dir = tmp_path / "media"
    _write_sections(
        media_dir,
        "TextHelpers",
        [
            {"name": "Intro", "type": "simplex.main", "video": "intro.mp4", "duration": "2.0"},
            {"name": "step1", "type": "simplex.sub", "video": "step1.mp4", "duration": 1.0},
            {"name": "step2", "type": "simplex.sub", "video": "step2.mp4", "duration": 1.5},
            {"name": "Setup", "type": "simplex.main", "video": "setup.mp4", "duration": 2.0},
            {"name": "step3", "type": "simplex.sub", "video": "step3.mp4", "duration": 0.5},
        ],
    )
    # Second scene with auto-created default.normal at the start.
    _write_sections(
        media_dir,
        "CodeHelpers",
        [
            {
                "name": "autocreated",
                "type": "default.normal",
                "video": "auto.mp4",
                "duration": 1.0,
            },
        ],
    )
    manifest = build_manifest(deck, media_dir=media_dir)
    assert manifest.slide_count == 3
    intro, setup, code = manifest.main_slides
    assert (intro.name, intro.index, len(intro.subsections)) == ("Intro", 1, 3)
    assert (setup.name, setup.index, len(setup.subsections)) == ("Setup", 2, 2)
    assert intro.duration_s == 4.5  # 2.0 + 1.0 + 1.5
    assert setup.duration_s == 2.5  # 2.0 + 0.5
    # default.normal-only scene: name is humanised scene name.
    assert (code.name, code.index, len(code.subsections)) == ("Code Helpers", 3, 1)


def test_leading_default_normal_absorbed_into_explicit_main(tmp_path: Path) -> None:
    """``self.play(); self.next_slide(name='X')`` -> one main 'X', no phantom."""
    deck = _deck(tmp_path)
    media_dir = tmp_path / "media"
    _write_sections(
        media_dir,
        "TextHelpers",
        [
            {"name": "autocreated", "type": "default.normal", "video": "auto.mp4", "duration": 0.8},
            {"name": "Intro", "type": "simplex.main", "video": "intro.mp4", "duration": 2.0},
            {"name": "step", "type": "simplex.sub", "video": "step.mp4", "duration": 1.0},
        ],
    )
    _write_sections(media_dir, "CodeHelpers", [])
    manifest = build_manifest(deck, media_dir=media_dir)
    # One main "Intro" (no phantom from the auto-created default.normal);
    # the absorbed leading section shows up as the main's first subsection.
    intro = manifest.main_slides[0]
    assert intro.name == "Intro"
    assert [sub.name for sub in intro.subsections] == ["autocreated", "Intro", "step"]
    # ``thumbnail_section_index=-2`` now points at the explicit main's frame,
    # which is exactly the user-visible "last visual state of the slide".
    assert intro.subsections[-2].name == "Intro"


def test_default_normal_kept_as_main_without_explicit_marker(tmp_path: Path) -> None:
    """No ``simplex.main`` follows -> default.normal stays as the implicit main."""
    deck = _deck(tmp_path)
    media_dir = tmp_path / "media"
    _write_sections(
        media_dir,
        "TextHelpers",
        [
            {"name": "auto", "type": "default.normal", "video": "auto.mp4", "duration": 1.0},
            {"name": "sub", "type": "simplex.sub", "video": "sub.mp4", "duration": 0.5},
        ],
    )
    _write_sections(media_dir, "CodeHelpers", [])
    manifest = build_manifest(deck, media_dir=media_dir)
    main = manifest.main_slides[0]
    # No explicit marker -> humanised scene name, default kept as the main.
    assert main.name == "Text Helpers"
    assert [sub.name for sub in main.subsections] == ["auto", "sub"]


def test_manifest_loop_type_preserved(tmp_path: Path) -> None:
    deck = _deck(tmp_path)
    media_dir = tmp_path / "media"
    _write_sections(
        media_dir,
        "TextHelpers",
        [
            {"name": "Looping", "type": "simplex.main.loop", "duration": 1.0},
            {"name": "sub", "type": "simplex.sub.loop", "duration": 0.5},
        ],
    )
    _write_sections(
        media_dir,
        "CodeHelpers",
        [{"name": "x", "type": "simplex.main", "duration": 0.1}],
    )
    manifest = build_manifest(deck, media_dir=media_dir)
    looping = manifest.main_slides[0]
    assert looping.section_type == "simplex.main.loop"
    assert looping.subsections[1].section_type == "simplex.sub.loop"
