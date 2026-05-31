"""`simplex render` flags: --scene filter, triple-syntax target."""

from pathlib import Path
from typing import Any

import pytest
from typer.testing import CliRunner

from simplex.cli import commands
from simplex.cli.commands import app


def _noop_export(deck: Any, *, output_dir: Path) -> None:
    pass


def _make_deck(decks_dir: Path) -> None:
    deck_dir = decks_dir / "demo"
    deck_dir.mkdir(parents=True)
    (deck_dir / "deck.toml").write_text(
        'slug = "demo"\ntitle = "Demo"\nentrypoints = ["slides.scenes:Foo", "slides.scenes:Bar"]\n',
        encoding="utf-8",
    )
    slides_pkg = deck_dir / "slides"
    slides_pkg.mkdir()
    (slides_pkg / "__init__.py").write_text("", encoding="utf-8")
    (slides_pkg / "scenes.py").write_text("class Foo: ...\nclass Bar: ...\n", encoding="utf-8")


@pytest.fixture
def stub_render(monkeypatch: pytest.MonkeyPatch) -> list[dict[str, Any]]:
    calls: list[dict[str, Any]] = []

    def fake_render(
        deck: Any,
        *,
        output_dir: Path,
        scenes: tuple[str, ...] = (),
        write_last_frame: bool = False,
    ) -> None:
        calls.append(
            {
                "deck": deck.slug,
                "theme": deck.theme,
                "output_dir": output_dir,
                "scenes": scenes,
                "write_last_frame": write_last_frame,
            }
        )

    monkeypatch.setattr(commands.runner, "render", fake_render)
    monkeypatch.setattr(commands.pdf, "export", _noop_export)
    return calls


@pytest.fixture
def project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    _make_deck(tmp_path / "decks")
    monkeypatch.chdir(tmp_path)
    return tmp_path


def test_render_calls_runner(project: Path, stub_render: list[dict[str, Any]]) -> None:
    result = CliRunner().invoke(app, ["render", "demo"])
    assert result.exit_code == 0, result.stdout
    assert len(stub_render) == 2
    assert {call["theme"] for call in stub_render} == {"simplex_dark", "simplex_light"}
    assert {call["scenes"] for call in stub_render} == {()}
    assert stub_render[0]["output_dir"].parts[-2:] == ("themes", "dark")


def test_render_scene_filter(project: Path, stub_render: list[dict[str, Any]]) -> None:
    result = CliRunner().invoke(app, ["render", "demo", "--scene", "Foo"])
    assert result.exit_code == 0, result.stdout
    assert {call["scenes"] for call in stub_render} == {("Foo",)}


def test_render_triple_syntax_scene(project: Path, stub_render: list[dict[str, Any]]) -> None:
    result = CliRunner().invoke(app, ["render", "demo::Foo"])
    assert result.exit_code == 0, result.stdout
    assert {call["scenes"] for call in stub_render} == {("Foo",)}


def test_render_can_limit_true_theme_variant(
    project: Path,
    stub_render: list[dict[str, Any]],
) -> None:
    result = CliRunner().invoke(app, ["render", "demo", "--slide-theme", "light"])
    assert result.exit_code == 0, result.stdout
    assert len(stub_render) == 1
    assert stub_render[0]["theme"] == "simplex_light"
    assert stub_render[0]["output_dir"].parts[-2:] == ("themes", "light")


def test_render_unknown_scene_fails(project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(
        deck: Any, *, output_dir: Path, scenes: tuple[str, ...] = (), write_last_frame: bool = False
    ) -> None:
        raise ValueError("unknown scene name(s): ['Ghost']")

    monkeypatch.setattr(commands.runner, "render", boom)
    monkeypatch.setattr(commands.pdf, "export", _noop_export)
    result = CliRunner().invoke(app, ["render", "demo", "--scene", "Ghost"])
    assert result.exit_code != 0


def test_clean_deck_removes_only_that_slug(
    project: Path, stub_render: list[dict[str, Any]]
) -> None:
    cli = CliRunner()
    site_dir = project / "site" / "decks" / "demo"
    site_dir.mkdir(parents=True, exist_ok=True)
    (site_dir / "marker").write_text("x", encoding="utf-8")

    other = project / "site" / "decks" / "other"
    other.mkdir(parents=True)
    (other / "marker").write_text("x", encoding="utf-8")

    result = cli.invoke(app, ["clean", "--deck", "demo"])
    assert result.exit_code == 0, result.stdout
    assert not site_dir.exists()
    assert other.exists()
