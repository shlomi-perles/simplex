"""runner.render: direct Manim subprocess invocation."""

import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from simplex.deck.config import DeckConfig
from simplex.render import runner
from simplex.render._warnings import PYDUB_SYNTAX_WARNING_FILTER


def _deck(tmp_path: Path) -> DeckConfig:
    deck_dir = tmp_path / "demo"
    deck_dir.mkdir()
    (deck_dir / "deck.toml").write_text(
        'slug = "demo"\n'
        'title = "Demo"\n'
        'theme = "simplex_light"\n'
        'entrypoints = ["slides.scenes:Foo", "slides.scenes:Bar"]\n',
        encoding="utf-8",
    )
    slides_pkg = deck_dir / "slides"
    slides_pkg.mkdir()
    (slides_pkg / "__init__.py").write_text("", encoding="utf-8")
    (slides_pkg / "scenes.py").write_text("class Foo: ...\nclass Bar: ...\n", encoding="utf-8")
    return DeckConfig.load(deck_dir)


def _opengl_deck(tmp_path: Path) -> DeckConfig:
    deck_dir = tmp_path / "demo"
    deck_dir.mkdir()
    (deck_dir / "deck.toml").write_text(
        'slug = "demo"\ntitle = "Demo"\nentrypoints = ["slides.surface:Surface@opengl"]\n',
        encoding="utf-8",
    )
    slides_pkg = deck_dir / "slides"
    slides_pkg.mkdir()
    (slides_pkg / "__init__.py").write_text("", encoding="utf-8")
    (slides_pkg / "surface.py").write_text("class Surface: ...\n", encoding="utf-8")
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


def test_render_invokes_python_manim_without_save_sections_and_internal_cache(
    tmp_path: Path, captured: list[dict[str, Any]]
) -> None:
    deck = _deck(tmp_path)
    runner.render(deck, output_dir=tmp_path / "out")

    args = captured[0]["args"]
    assert args[:3] == [sys.executable, "-m", "manim"]
    assert "--save_sections" not in args
    assert "--disable_caching" in args
    assert "--media_dir" in args
    assert args[-2:] == ["Foo", "Bar"]


def test_render_does_not_inject_save_sections_into_merged_config(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = tmp_path / "project"
    deck_dir = project / "decks" / "demo"
    deck_dir.mkdir(parents=True)
    (project / "manim.cfg").write_text("[CLI]\nplugins = simplex\n", encoding="utf-8")
    (deck_dir / "deck.toml").write_text(
        'slug = "demo"\ntitle = "Demo"\nentrypoints = ["slides.scenes:Foo"]\n',
        encoding="utf-8",
    )
    slides_pkg = deck_dir / "slides"
    slides_pkg.mkdir()
    (slides_pkg / "__init__.py").write_text("", encoding="utf-8")
    (slides_pkg / "scenes.py").write_text("class Foo: ...\n", encoding="utf-8")
    deck = DeckConfig.load(deck_dir)
    merged_configs: list[str] = []

    def fake_run(args: list[str], **kwargs: Any) -> Any:
        cfg = Path(args[args.index("--config_file") + 1])
        merged_configs.append(cfg.read_text(encoding="utf-8"))

        class _Done:
            returncode = 0

        return _Done()

    monkeypatch.setattr(runner.subprocess, "run", fake_run)
    runner.render(deck, output_dir=tmp_path / "out")

    assert "plugins = simplex" in merged_configs[0]
    assert "save_sections" not in merged_configs[0]


def test_render_respects_user_cache_control_arg(
    tmp_path: Path,
    captured: list[dict[str, Any]],
) -> None:
    deck = _deck(tmp_path)
    runner.render(deck, output_dir=tmp_path / "out", manim_args=("--flush_cache",))

    args = captured[0]["args"]
    assert "--flush_cache" in args
    assert "--disable_caching" not in args


def test_runner_module_does_not_import_manim() -> None:
    subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys; import simplex.render.runner; assert 'manim' not in sys.modules",
        ],
        check=True,
    )


def test_render_sets_cue_env_and_utf8(tmp_path: Path, captured: list[dict[str, Any]]) -> None:
    deck = _deck(tmp_path)
    runner.render(deck, output_dir=tmp_path / "out")
    env = captured[0]["env"]

    assert env["SIMPLEX_THEME"] == "simplex_light"
    assert env["SIMPLEX_CUES_DIR"] == str((tmp_path / "out" / "simplex-cues").resolve())
    assert env["PYTHONIOENCODING"] == "utf-8"
    assert env["PYTHONUTF8"] == "1"
    assert PYDUB_SYNTAX_WARNING_FILTER in env["PYTHONWARNINGS"]


def test_render_drops_interpreter_steering_env_vars(
    tmp_path: Path,
    captured: list[dict[str, Any]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PYTHONPATH", "foreign")
    monkeypatch.setenv("PYTHONHOME", "foreign")
    monkeypatch.setenv("VIRTUAL_ENV", "foreign")

    runner.render(_deck(tmp_path), output_dir=tmp_path / "out")

    env = captured[0]["env"]
    assert "PYTHONPATH" not in env
    assert "PYTHONHOME" not in env
    assert "VIRTUAL_ENV" not in env


def test_render_scenes_filter_keeps_subset(tmp_path: Path, captured: list[dict[str, Any]]) -> None:
    runner.render(_deck(tmp_path), output_dir=tmp_path / "out", scenes=("Bar",))
    args = captured[0]["args"]
    assert args[-1] == "Bar"
    assert "Foo" not in args


def test_render_unknown_scene_raises(tmp_path: Path, captured: list[dict[str, Any]]) -> None:
    with pytest.raises(ValueError, match="unknown scene"):
        runner.render(_deck(tmp_path), output_dir=tmp_path / "out", scenes=("Ghost",))
    assert captured == []


def test_render_opengl_entrypoint_adds_renderer_and_movie_flags(
    tmp_path: Path,
    captured: list[dict[str, Any]],
) -> None:
    runner.render(_opengl_deck(tmp_path), output_dir=tmp_path / "out")
    args = captured[0]["args"]
    assert "--renderer=opengl" in args
    assert "--write_to_movie" in args
    assert args[-1] == "Surface"
