"""`simplex render` flags: --force, --scene, cache freshness."""

from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from typer.testing import CliRunner

from simplex.cli import commands
from simplex.cli.commands import app


def _make_deck(decks_dir: Path) -> None:
    deck_dir = decks_dir / "demo"
    deck_dir.mkdir(parents=True)
    (deck_dir / "deck.toml").write_text(
        'slug = "demo"\n'
        'title = "Demo"\n'
        'entrypoints = ["slides.scenes:Foo", "slides.scenes:Bar"]\n',
        encoding="utf-8",
    )
    slides_pkg = deck_dir / "slides"
    slides_pkg.mkdir()
    (slides_pkg / "__init__.py").write_text("", encoding="utf-8")
    (slides_pkg / "scenes.py").write_text(
        "class Foo: ...\nclass Bar: ...\n", encoding="utf-8"
    )


@pytest.fixture
def stub_render(monkeypatch: pytest.MonkeyPatch) -> Iterator[list[dict[str, Any]]]:
    calls: list[dict[str, Any]] = []

    def fake_render(deck: Any, *, output_dir: Path, scenes: tuple[str, ...] = ()) -> None:
        calls.append({"deck": deck.slug, "output_dir": output_dir, "scenes": scenes})

    monkeypatch.setattr(commands.runner, "render", fake_render)
    monkeypatch.setattr(commands.pdf, "export", lambda deck, output_dir: None)
    yield calls


@pytest.fixture
def project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    _make_deck(tmp_path / "decks")
    monkeypatch.chdir(tmp_path)
    return tmp_path


def test_render_default_skips_when_fresh(
    project: Path, stub_render: list[dict[str, Any]]
) -> None:
    cli = CliRunner()
    cli.invoke(app, ["render", "demo"])
    assert len(stub_render) == 1

    # Second invocation hits the cache and should not re-render.
    result = cli.invoke(app, ["render", "demo"])
    assert result.exit_code == 0
    assert "cached" in result.stdout
    assert len(stub_render) == 1


def test_render_force_ignores_cache(
    project: Path, stub_render: list[dict[str, Any]]
) -> None:
    cli = CliRunner()
    cli.invoke(app, ["render", "demo"])
    cli.invoke(app, ["render", "demo", "--force"])
    assert len(stub_render) == 2
    assert all(c["scenes"] == () for c in stub_render)


def test_render_scene_filters_and_clears_stamp(
    project: Path, stub_render: list[dict[str, Any]]
) -> None:
    cli = CliRunner()
    cli.invoke(app, ["render", "demo"])  # mark fresh

    cache_dir = project / ".simplex_cache"
    stamps_before = list(cache_dir.glob("demo.*.stamp"))
    assert len(stamps_before) == 1

    result = cli.invoke(app, ["render", "demo", "--scene", "Foo"])
    assert result.exit_code == 0, result.stdout
    assert stub_render[-1]["scenes"] == ("Foo",)

    # Partial render must clear the stamp so the next full run re-renders.
    stamps_after = list(cache_dir.glob("demo.*.stamp"))
    assert stamps_after == []


def test_render_unknown_scene_fails(
    project: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def boom(deck: Any, *, output_dir: Path, scenes: tuple[str, ...] = ()) -> None:
        raise ValueError("unknown scene name(s): ['Ghost']")

    monkeypatch.setattr(commands.runner, "render", boom)
    monkeypatch.setattr(commands.pdf, "export", lambda deck, output_dir: None)
    result = CliRunner().invoke(app, ["render", "demo", "--scene", "Ghost"])
    assert result.exit_code != 0


def test_clean_deck_removes_only_that_slug(
    project: Path, stub_render: list[dict[str, Any]]
) -> None:
    # Render to produce a site dir + cache stamp.
    cli = CliRunner()
    site_dir = project / "site" / "decks" / "demo"
    site_dir.mkdir(parents=True, exist_ok=True)
    (site_dir / "marker").write_text("x", encoding="utf-8")
    cli.invoke(app, ["render", "demo"])
    cache_dir = project / ".simplex_cache"
    assert list(cache_dir.glob("demo.*.stamp"))

    # Create a second deck whose state must be preserved.
    other = project / "site" / "decks" / "other"
    other.mkdir(parents=True)
    (other / "marker").write_text("x", encoding="utf-8")

    result = cli.invoke(app, ["clean", "--deck", "demo"])
    assert result.exit_code == 0, result.stdout
    assert not site_dir.exists()
    assert other.exists()
    assert list(cache_dir.glob("demo.*.stamp")) == []
