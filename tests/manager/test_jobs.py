"""Manager job command construction and post-render output selection."""

import inspect
import sys
from pathlib import Path

import pytest

from simplex.manager.jobs import (
    JobRequest,
    _shell_execute_foreground,
    command_for_request,
    job_name_for_request,
    manager_opens_after_success,
    open_target_for_request,
)
from simplex.render.runner import _manim_command


def _write_deck(root: Path, *, opengl: bool = False) -> None:
    (root / "site.toml").write_text('brand = "Demo"\n', encoding="utf-8")
    deck = root / "decks" / "demo"
    deck.mkdir(parents=True)
    entrypoint = "slides.surface:Surface@opengl" if opengl else "slides.scenes:Foo"
    (deck / "deck.toml").write_text(
        f'slug = "demo"\ntitle = "Demo"\nentrypoints = ["{entrypoint}"]\n',
        encoding="utf-8",
    )
    slides = deck / "slides"
    slides.mkdir()
    (slides / "__init__.py").write_text("", encoding="utf-8")
    if opengl:
        (slides / "surface.py").write_text(
            "from simplex.slides import ThreeDSlide\n\nclass Surface(ThreeDSlide):\n    pass\n",
            encoding="utf-8",
        )
    else:
        (slides / "scenes.py").write_text(
            "from simplex.slides import Slide\n\nclass Foo(Slide):\n    pass\n",
            encoding="utf-8",
        )


def test_cairo_scene_open_after_uses_manager_output_open(tmp_path: Path) -> None:
    _write_deck(tmp_path)

    command = command_for_request(
        tmp_path,
        JobRequest(
            action="render_scene",
            deck_slug="demo",
            scene="Foo",
            open_after=True,
            cache="on",
        ),
    )

    assert "-p" not in command
    assert "--disable_caching" not in command
    assert command[1:3] == ("-m", "simplex.manager.run_cli")
    assert manager_opens_after_success(
        tmp_path,
        JobRequest(
            action="render_scene",
            deck_slug="demo",
            scene="Foo",
            open_after=True,
        ),
    )


def test_opengl_scene_preview_does_not_use_live_preview_flag(tmp_path: Path) -> None:
    _write_deck(tmp_path, opengl=True)

    command = command_for_request(
        tmp_path,
        JobRequest(
            action="render_scene",
            deck_slug="demo",
            scene="Surface",
            open_after=True,
            quality="low_quality",
            cache="off",
        ),
    )

    assert "-p" not in command
    assert (command[command.index("-q")], command[command.index("-q") + 1]) == ("-q", "l")
    assert "--disable_caching" in command
    assert manager_opens_after_success(
        tmp_path,
        JobRequest(
            action="render_scene",
            deck_slug="demo",
            scene="Surface",
            open_after=True,
        ),
    )


def test_flush_cache_is_forwarded_only_when_selected(tmp_path: Path) -> None:
    _write_deck(tmp_path)

    command = command_for_request(
        tmp_path,
        JobRequest(action="render_deck", deck_slug="demo", cache="flush"),
    )

    assert "--flush_cache" in command
    assert "--disable_caching" not in command


def test_open_target_for_scene_finds_specific_scene_output(tmp_path: Path) -> None:
    _write_deck(tmp_path, opengl=True)
    output = (
        tmp_path
        / ".simplex_cache"
        / "decks"
        / "demo"
        / "dark"
        / "intermediate"
        / "videos"
        / "surface"
        / "480p15"
        / "Surface.mp4"
    )
    output.parent.mkdir(parents=True)
    output.write_bytes(b"mp4")

    target = open_target_for_request(
        tmp_path,
        JobRequest(
            action="render_scene",
            deck_slug="demo",
            scene="Surface",
            slide_theme="dark",
            open_after=True,
        ),
    )

    assert target == output


def test_scene_job_name_is_slide_name(tmp_path: Path) -> None:
    _write_deck(tmp_path)

    name = job_name_for_request(
        tmp_path,
        JobRequest(action="render_scene", deck_slug="demo", scene="Foo"),
    )

    assert name == "Foo"


def test_windows_opener_uses_user32_wait_for_input_idle() -> None:
    source = inspect.getsource(_shell_execute_foreground)

    assert "user32.WaitForInputIdle" in source
    assert "kernel32.WaitForInputIdle" not in source


def test_manager_env_routes_manim_through_ansi_wrapper(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SIMPLEX_MANAGER_FORCE_ANSI", "1")

    assert _manim_command() == [sys.executable, "-m", "simplex.manager.run_manim"]
