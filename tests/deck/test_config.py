"""DeckConfig loading and slug validation."""

from datetime import date
from pathlib import Path

import pytest
from pydantic import ValidationError

from simplex.deck.config import DeckConfig, detect_source_renderer
from simplex.theme.styles.simplex_pycharm import SimplexPycharm
from simplex.theme.styles.simplex_solarized_light import SimplexSolarizedLight


def _write_toml(tmp_path: Path, body: str) -> Path:
    (tmp_path / "deck.toml").write_text(body, encoding="utf-8")
    return tmp_path


def test_load_minimal(tmp_path: Path) -> None:
    deck_dir = _write_toml(tmp_path, 'slug = "demo"\ntitle = "Demo"\n')
    cfg = DeckConfig.load(deck_dir)
    assert cfg.slug == "demo"
    assert cfg.title == "Demo"
    assert cfg.theme == "simplex_dark"
    assert cfg.quality == "high_quality"


def test_invalid_slug_raises(tmp_path: Path) -> None:
    deck_dir = _write_toml(tmp_path, 'slug = "Bad_Slug"\ntitle = "x"\n')
    with pytest.raises(ValidationError):
        DeckConfig.load(deck_dir)


def test_frozen(tmp_path: Path) -> None:
    deck_dir = _write_toml(tmp_path, 'slug = "demo"\ntitle = "Demo"\n')
    cfg = DeckConfig.load(deck_dir)
    with pytest.raises(ValidationError):
        cfg.title = "other"  # type: ignore[misc]


def test_web_chrome_defaults_off(tmp_path: Path) -> None:
    """The presentation-chrome toggles default to off so legacy decks
    don't suddenly grow a clock or slide counter."""
    deck_dir = _write_toml(tmp_path, 'slug = "demo"\ntitle = "Demo"\n')
    cfg = DeckConfig.load(deck_dir)
    assert cfg.web.show_clock is False
    assert cfg.web.show_slide_number is False
    assert cfg.web.show_stopwatch is False
    assert cfg.resolved_notes_code_style() is SimplexSolarizedLight


def test_web_chrome_can_be_enabled(tmp_path: Path) -> None:
    deck_dir = _write_toml(
        tmp_path,
        'slug = "demo"\ntitle = "Demo"\n\n[web]\n'
        "show_clock = true\n"
        "show_slide_number = true\n"
        "show_stopwatch = true\n"
        'notes_code_style = "simplex_pycharm"\n',
    )
    cfg = DeckConfig.load(deck_dir)
    assert cfg.web.show_clock is True
    assert cfg.web.show_slide_number is True
    assert cfg.web.show_stopwatch is True
    assert cfg.resolved_notes_code_style() is SimplexPycharm


def test_created_at_and_carousel_gif_options_load(tmp_path: Path) -> None:
    deck_dir = _write_toml(
        tmp_path,
        'slug = "demo"\n'
        'title = "Demo"\n'
        'created_at = "2026-05-19"\n'
        "\n"
        "[web]\n"
        'carousel_gif = "preview.gif"\n'
        "carousel_gif_slides = [1, 3]\n",
    )
    cfg = DeckConfig.load(deck_dir)
    assert cfg.created_at == date(2026, 5, 19)
    assert cfg.web.carousel_gif == Path("preview.gif")
    assert cfg.web.carousel_gif_slides == (1, 3)


def test_string_entrypoints_load_as_cairo_shorthand(tmp_path: Path) -> None:
    deck_dir = _write_toml(
        tmp_path,
        'slug = "demo"\ntitle = "Demo"\nentrypoints = ["slides.intro:Intro"]\n',
    )
    slides_dir = deck_dir / "slides"
    slides_dir.mkdir()
    (slides_dir / "intro.py").write_text("", encoding="utf-8")

    cfg = DeckConfig.load(deck_dir)

    assert cfg.scene_specs == ("slides.intro:Intro",)
    assert cfg.resolve_entrypoints()[0].renderer == "cairo"


def test_structured_entrypoint_renderer_loads(tmp_path: Path) -> None:
    deck_dir = _write_toml(
        tmp_path,
        'slug = "demo"\n'
        'title = "Demo"\n'
        "\n"
        "[[entrypoints]]\n"
        'target = "slides.surface:Surface"\n'
        'renderer = "opengl"\n',
    )
    slides_dir = deck_dir / "slides"
    slides_dir.mkdir()
    (slides_dir / "surface.py").write_text("", encoding="utf-8")

    cfg = DeckConfig.load(deck_dir)
    group = cfg.resolve_entrypoints()[0]

    assert cfg.scene_specs == ("slides.surface:Surface",)
    assert group.renderer == "opengl"
    assert group.scene_names == ("Surface",)


def test_source_renderer_fallback_detects_top_level_config(tmp_path: Path) -> None:
    source = tmp_path / "scene.py"
    source.write_text(
        'from manim import config\nconfig.renderer = "opengl"\nconfig.write_to_movie = True\n',
        encoding="utf-8",
    )

    assert detect_source_renderer(source) == "opengl"


def test_entrypoint_renderer_conflict_raises(tmp_path: Path) -> None:
    deck_dir = _write_toml(
        tmp_path,
        'slug = "demo"\n'
        'title = "Demo"\n'
        "\n"
        "[[entrypoints]]\n"
        'target = "slides.surface:Surface"\n'
        'renderer = "cairo"\n',
    )
    slides_dir = deck_dir / "slides"
    slides_dir.mkdir()
    (slides_dir / "surface.py").write_text(
        'from manim import config\nconfig.renderer = "opengl"\n',
        encoding="utf-8",
    )
    cfg = DeckConfig.load(deck_dir)

    with pytest.raises(ValueError, match="declares renderer"):
        cfg.resolve_entrypoints()
