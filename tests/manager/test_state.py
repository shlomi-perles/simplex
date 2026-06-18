"""Manager deck state, entrypoint editing, and Manim option helpers."""

import tomllib
from pathlib import Path

from manim.constants import QUALITIES

from simplex.deck.config import DeckConfig
from simplex.manager.state import (
    available_quality_options,
    load_manager_state,
    manim_args_for_options,
    update_deck_defaults,
    update_deck_entrypoints,
)


def _write_project(root: Path) -> Path:
    (root / "site.toml").write_text('brand = "Demo"\n', encoding="utf-8")
    deck_dir = root / "decks" / "demo"
    deck_dir.mkdir(parents=True)
    (deck_dir / "deck.toml").write_text(
        'slug = "demo"\n'
        'title = "Demo"\n'
        'entrypoints = ["slides.scenes:Foo", "slides.surface:Surface@opengl"]\n',
        encoding="utf-8",
    )
    slides = deck_dir / "slides"
    slides.mkdir()
    (slides / "__init__.py").write_text("", encoding="utf-8")
    (slides / "scenes.py").write_text(
        "from simplex.slides import Slide\n\n"
        "class Foo(Slide):\n    pass\n\n"
        "class Bar(Slide):\n    pass\n",
        encoding="utf-8",
    )
    (slides / "surface.py").write_text(
        "from manim import config\nfrom simplex.slides import ThreeDSlide\n"
        'config.renderer = "opengl"\n\n'
        "class Surface(ThreeDSlide):\n    pass\n",
        encoding="utf-8",
    )
    return deck_dir


def test_update_entrypoints_keeps_current_string_convention(tmp_path: Path) -> None:
    deck_dir = _write_project(tmp_path)

    update_deck_entrypoints(
        tmp_path,
        "demo",
        ("slides.surface:Surface@opengl", "slides.scenes:Bar"),
    )

    text = (deck_dir / "deck.toml").read_text(encoding="utf-8")
    raw = tomllib.loads(text)
    cfg = DeckConfig.load(deck_dir)

    assert raw["entrypoints"] == ["slides.surface:Surface@opengl", "slides.scenes:Bar"]
    assert "[[entrypoints]]" not in text
    assert cfg.scene_specs == ("slides.surface:Surface", "slides.scenes:Bar")
    assert cfg.resolve_entrypoints()[0].renderer == "opengl"


def test_manager_state_shows_available_unconfigured_scenes(tmp_path: Path) -> None:
    _write_project(tmp_path)

    state = load_manager_state(tmp_path)
    deck = state["decks"][0]  # type: ignore[index]
    available = {entry["value"] for entry in deck["available"]}  # type: ignore[index]

    assert "slides.scenes:Bar" in available
    assert "slides.scenes:Foo" not in available


def test_manager_state_includes_deck_defaults_editor_schema(tmp_path: Path) -> None:
    _write_project(tmp_path)

    state = load_manager_state(tmp_path)
    option_paths = {option["path"] for option in state["deckOptions"]}  # type: ignore[index]
    deck = state["decks"][0]  # type: ignore[index]
    defaults = deck["defaults"]  # type: ignore[index]

    assert "theme" in option_paths
    assert "slide_themes.enabled" in option_paths
    assert "packaging.hls_segment_duration" in option_paths
    assert defaults["title"]["value"] == "Demo"  # type: ignore[index]


def test_update_deck_defaults_writes_only_non_default_values(tmp_path: Path) -> None:
    deck_dir = _write_project(tmp_path)

    update_deck_defaults(
        tmp_path,
        "demo",
        {
            "title": "Better Demo",
            "summary": "",
            "theme": "simplex_dark",
            "web.show_clock": True,
            "web.controls": True,
            "slide_themes.enabled": False,
            "packaging.hls_segment_duration": 6,
        },
    )

    raw = tomllib.loads((deck_dir / "deck.toml").read_text(encoding="utf-8"))

    assert raw["title"] == "Better Demo"
    assert "summary" not in raw
    assert "theme" not in raw
    assert raw["entrypoints"] == ["slides.scenes:Foo", "slides.surface:Surface@opengl"]
    assert raw["web"] == {"show_clock": True}
    assert raw["slide_themes"] == {"enabled": False}
    assert raw["packaging"] == {"hls_segment_duration": 6}


def test_manim_args_keep_cache_on_as_no_flag() -> None:
    assert "--disable_caching" not in manim_args_for_options(cache="on")
    assert manim_args_for_options(cache="off") == ("--disable_caching",)
    assert manim_args_for_options(cache="flush") == ("--flush_cache",)


def test_quality_options_are_derived_from_manim_constants() -> None:
    options = available_quality_options()
    flags = {option["name"]: option["flag"] for option in options}

    assert flags["low_quality"] == QUALITIES["low_quality"]["flag"]
    assert manim_args_for_options(quality="low_quality") == (
        "-q",
        QUALITIES["low_quality"]["flag"],
    )
