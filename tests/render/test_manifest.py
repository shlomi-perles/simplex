"""DeckManifest: parse manim-slides JSON, degrade to synthetic refs."""

import json
from pathlib import Path

from simplex.deck.config import DeckConfig
from simplex.render.manifest import build_manifest


def _deck(tmp_path: Path, scenes: tuple[str, ...]) -> DeckConfig:
    deck_dir = tmp_path / "demo"
    deck_dir.mkdir(parents=True, exist_ok=True)
    scenes_toml = ", ".join(f'"{s}"' for s in scenes)
    (deck_dir / "deck.toml").write_text(
        f'slug = "demo"\ntitle = "Demo"\nscenes = [{scenes_toml}]\n',
        encoding="utf-8",
    )
    (deck_dir / "slides.py").write_text("# empty\n", encoding="utf-8")
    return DeckConfig.load(deck_dir)


def test_manifest_synthetic_when_no_json(tmp_path: Path) -> None:
    deck = _deck(tmp_path, ("Intro", "Body", "Outro"))
    media_dir = tmp_path / "media"
    media_dir.mkdir()
    manifest = build_manifest(deck, media_dir=media_dir)
    assert manifest.slide_count == 3
    assert [s.scene for s in manifest.slides] == ["Intro", "Body", "Outro"]
    assert manifest.slides[0].title == "Intro"


def test_manifest_parses_per_scene_json(tmp_path: Path) -> None:
    deck = _deck(tmp_path, ("Intro", "Body"))
    media_dir = tmp_path / "media"
    slides_dir = media_dir / "slides"
    slides_dir.mkdir(parents=True)
    (slides_dir / "Intro.json").write_text(
        json.dumps({"slides": [{"file": "Intro_0.mp4"}, {"file": "Intro_1.mp4"}]}),
        encoding="utf-8",
    )
    (slides_dir / "Body.json").write_text(
        json.dumps({"slides": [{"file": "Body_0.mp4"}]}),
        encoding="utf-8",
    )
    manifest = build_manifest(deck, media_dir=media_dir)
    assert manifest.slide_count == 3
    assert [s.scene for s in manifest.slides] == ["Intro", "Intro", "Body"]
    # Files don't exist on disk so video_paths is empty; resolver guards that.
    assert all(s.video_paths == () for s in manifest.slides)


def test_manifest_ignores_unknown_scene_json(tmp_path: Path) -> None:
    deck = _deck(tmp_path, ("Intro",))
    media_dir = tmp_path / "media"
    slides_dir = media_dir / "slides"
    slides_dir.mkdir(parents=True)
    (slides_dir / "Intro.json").write_text(
        json.dumps({"slides": [{"file": "Intro_0.mp4"}]}),
        encoding="utf-8",
    )
    (slides_dir / "OtherScene.json").write_text(
        json.dumps({"slides": [{"file": "x.mp4"}]}),
        encoding="utf-8",
    )
    manifest = build_manifest(deck, media_dir=media_dir)
    assert [s.scene for s in manifest.slides] == ["Intro"]
