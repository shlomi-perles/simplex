"""runner.render: subprocess invocation, --save_sections flag, scene filtering."""

from pathlib import Path
from typing import Any

import pytest

from simplex.deck.config import DeckConfig
from simplex.render import runner


def _deck(tmp_path: Path) -> DeckConfig:
    deck_dir = tmp_path / "demo"
    deck_dir.mkdir()
    (deck_dir / "deck.toml").write_text(
        'slug = "demo"\n'
        'title = "Demo"\n'
        'theme = "academic_light"\n'
        'quality = "low_quality"\n'
        'entrypoints = ["slides.scenes:Foo", "slides.scenes:Bar"]\n',
        encoding="utf-8",
    )
    slides_pkg = deck_dir / "slides"
    slides_pkg.mkdir()
    (slides_pkg / "__init__.py").write_text("", encoding="utf-8")
    (slides_pkg / "scenes.py").write_text("class Foo: ...\nclass Bar: ...\n", encoding="utf-8")
    return DeckConfig.load(deck_dir)


@pytest.fixture
def captured(monkeypatch: pytest.MonkeyPatch) -> list[dict[str, Any]]:
    calls: list[dict[str, Any]] = []

    def fake_run(args: list[str], **kwargs: Any) -> Any:
        calls.append({"args": args, **kwargs})

        class _Done:
            returncode = 0

        return _Done()

    monkeypatch.setattr(runner.subprocess, "run", fake_run)
    return calls


def test_render_passes_save_sections(tmp_path: Path, captured: list[dict[str, Any]]) -> None:
    deck = _deck(tmp_path)
    runner.render(deck, output_dir=tmp_path / "out")
    assert len(captured) == 1
    args = captured[0]["args"]
    assert "--save_sections" in args


def test_render_passes_all_scenes_when_filter_empty(
    tmp_path: Path, captured: list[dict[str, Any]]
) -> None:
    deck = _deck(tmp_path)
    runner.render(deck, output_dir=tmp_path / "out")
    args = captured[0]["args"]
    assert args[-2:] == ["Foo", "Bar"]


def test_render_scenes_filter_keeps_subset(tmp_path: Path, captured: list[dict[str, Any]]) -> None:
    deck = _deck(tmp_path)
    runner.render(deck, output_dir=tmp_path / "out", scenes=("Bar",))
    assert len(captured) == 1
    args = captured[0]["args"]
    assert args[-1] == "Bar"
    assert "Foo" not in args


def test_render_unknown_scene_raises(tmp_path: Path, captured: list[dict[str, Any]]) -> None:
    deck = _deck(tmp_path)
    with pytest.raises(ValueError, match="unknown scene"):
        runner.render(deck, output_dir=tmp_path / "out", scenes=("Ghost",))
    assert captured == []


def test_render_write_last_frame_adds_flag(tmp_path: Path, captured: list[dict[str, Any]]) -> None:
    deck = _deck(tmp_path)
    runner.render(deck, output_dir=tmp_path / "out", write_last_frame=True)
    args = captured[0]["args"]
    # Manim 0.20 spells the smoke-render flag ``--save_last_frame``.
    assert "--save_last_frame" in args


def test_render_caching_disabled_adds_flag(tmp_path: Path, captured: list[dict[str, Any]]) -> None:
    deck = _deck(tmp_path).model_copy(update={"caching": False})
    runner.render(deck, output_dir=tmp_path / "out")
    args = captured[0]["args"]
    assert "--disable_caching" in args
