"""runner.render: subprocess invocation, passthrough flags, scene filtering."""

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


def test_render_passes_save_sections(tmp_path: Path, captured: list[dict[str, Any]]) -> None:
    deck = _deck(tmp_path)
    runner.render(deck, output_dir=tmp_path / "out")
    assert len(captured) == 1
    args = captured[0]["args"]
    assert "--save_sections" in args
    assert "--media_dir" in args
    assert args[args.index("--media_dir") + 1] == str((tmp_path / "out").resolve())


def test_runner_module_does_not_import_manim() -> None:
    subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "import simplex.render.runner; "
                "assert 'manim' not in sys.modules; "
                "assert 'manim.constants' not in sys.modules"
            ),
        ],
        check=True,
    )


def test_render_finds_manim_slides_next_to_python(
    tmp_path: Path,
    captured: list[dict[str, Any]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    scripts_dir = tmp_path / "venv" / "Scripts"
    scripts_dir.mkdir(parents=True)
    python_exe = scripts_dir / "python.exe"
    script_name = "manim-slides.exe" if runner.os.name == "nt" else "manim-slides"
    manim_slides = scripts_dir / script_name
    python_exe.write_text("", encoding="utf-8")
    manim_slides.write_text("", encoding="utf-8")

    def fake_which(_name: str) -> None:
        return None

    monkeypatch.setattr(runner.shutil, "which", fake_which)
    monkeypatch.setattr(runner.sys, "executable", str(python_exe))

    deck = _deck(tmp_path)
    runner.render(deck, output_dir=tmp_path / "out")

    assert captured[0]["args"][0] == str(manim_slides)


def test_render_forces_utf8_subprocess_env(tmp_path: Path, captured: list[dict[str, Any]]) -> None:
    deck = _deck(tmp_path)
    runner.render(deck, output_dir=tmp_path / "out")
    env = captured[0]["env"]
    assert env["SIMPLEX_THEME"] == "simplex_light"
    assert env["SIMPLEX_PROJECT_ROOT"] == str(Path.cwd().resolve())
    assert env["SIMPLEX_SLIDES_DIR"] == str((tmp_path / "out" / "slides").resolve())
    assert env["PYTHONIOENCODING"] == "utf-8"
    assert env["PYTHONUTF8"] == "1"
    assert captured[0]["cwd"] == deck.path.resolve()


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


def test_render_filters_pydub_syntax_warning(
    tmp_path: Path,
    captured: list[dict[str, Any]],
) -> None:
    deck = _deck(tmp_path)
    runner.render(deck, output_dir=tmp_path / "out")
    env = captured[0]["env"]

    assert PYDUB_SYNTAX_WARNING_FILTER in env["PYTHONWARNINGS"]


def test_render_preserves_existing_pythonwarnings(
    tmp_path: Path,
    captured: list[dict[str, Any]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PYTHONWARNINGS", "default")
    deck = _deck(tmp_path)
    runner.render(deck, output_dir=tmp_path / "out")
    env = captured[0]["env"]

    assert env["PYTHONWARNINGS"].startswith("default,")
    assert env["PYTHONWARNINGS"].endswith(PYDUB_SYNTAX_WARNING_FILTER)


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
    assert "--from_animation_number" in args
    assert args[args.index("--from_animation_number") + 1] == "0,0"
    assert "--save_last_frame" not in args


def test_render_forwards_manim_args_before_simplex_invariants(
    tmp_path: Path,
    captured: list[dict[str, Any]],
) -> None:
    deck = _deck(tmp_path)
    runner.render(
        deck, output_dir=tmp_path / "out", manim_args=("--disable_caching", "--fps", "60")
    )
    args = captured[0]["args"]
    assert "--disable_caching" in args
    assert args[args.index("--fps") + 1] == "60"
    assert args.index("--disable_caching") < args.index("--media_dir")
    assert args.index("--fps") < args.index("--media_dir")
    assert args.index("--save_sections") > args.index("--media_dir")


def test_render_opengl_entrypoint_adds_renderer_and_movie_flags(
    tmp_path: Path,
    captured: list[dict[str, Any]],
) -> None:
    deck = _opengl_deck(tmp_path)
    runner.render(deck, output_dir=tmp_path / "out", manim_args=("--renderer=cairo",))
    args = captured[0]["args"]

    assert args.index("--renderer=cairo") < args.index("--renderer=opengl")
    assert "--renderer=opengl" in args
    assert "--write_to_movie" in args
    assert args[-1] == "Surface"


def test_render_skip_renderer_omits_matching_groups(
    tmp_path: Path,
    captured: list[dict[str, Any]],
) -> None:
    deck = _opengl_deck(tmp_path)
    runner.render(deck, output_dir=tmp_path / "out", skip_renderers=("opengl",))

    assert captured == []
