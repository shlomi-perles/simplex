"""Repo-local Simplex theme JSON files."""

import json
from pathlib import Path

import pytest

from simplex.theme import presets
from simplex.theme.styles.simplex_pycharm import SimplexPycharm


def test_custom_theme_json_can_override_semantic_palette(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    theme_dir = tmp_path / "simplex_themes" / "themes"
    theme_dir.mkdir(parents=True)
    (theme_dir / "lecture_light.json").write_text(
        json.dumps(
            {
                "manim_palette": "simplex_light",
                "code_style": "simplex_pycharm",
                "palette": {
                    "background": "#FAF8EC",
                    "font": "#202020",
                    "vertex": "#123456",
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("SIMPLEX_PROJECT_ROOT", str(tmp_path))

    theme = presets.get("lecture_light")

    assert theme.name == "lecture_light"
    assert theme.manim_palette == "simplex_light"
    assert theme.code_style is SimplexPycharm
    assert theme.palette.background == "#FAF8EC"
    assert theme.palette.font == "#202020"
    assert theme.palette.vertex == "#123456"
    assert theme.palette.vertex_stroke == "#426A79"
    assert theme.web_palette.background == "#FAF8EC"
    assert theme.web_palette.text_primary == "#202020"


def test_custom_theme_json_can_omit_manim_palette(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    theme_dir = tmp_path / "simplex_themes" / "themes"
    theme_dir.mkdir(parents=True)
    (theme_dir / "dark_variant.json").write_text(
        json.dumps({"palette": {"background": "#111111", "font": "#EEEEEE"}}),
        encoding="utf-8",
    )
    monkeypatch.setenv("SIMPLEX_PROJECT_ROOT", str(tmp_path))

    theme = presets.get("dark_variant")

    assert theme.manim_palette is None
    assert theme.palette.background == "#111111"
    assert theme.palette.font == "#EEEEEE"
    assert theme.palette.vertex_stroke == "#58C4DD"
    assert theme.web_palette.background == "#111111"
    assert theme.web_palette.text_primary == "#EEEEEE"


def test_available_theme_names_includes_custom_json(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    theme_dir = tmp_path / "simplex_themes" / "themes"
    theme_dir.mkdir(parents=True)
    (theme_dir / "my_theme.json").write_text("{}", encoding="utf-8")
    monkeypatch.setenv("SIMPLEX_PROJECT_ROOT", str(tmp_path))

    assert "my_theme" in presets.available_names()


def test_custom_theme_dual_palette_values_use_requested_variant(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    theme_dir = tmp_path / "simplex_themes" / "themes"
    theme_dir.mkdir(parents=True)
    (theme_dir / "lecture.json").write_text(
        json.dumps(
            {
                "palette": {
                    "background": {"light": "#FFFFFF", "dark": "#000000"},
                    "font": {"light": "#111111", "dark": "#EEEEEE"},
                    "accent": {"light": "#0055AA", "dark": "#FFD166"},
                }
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("SIMPLEX_PROJECT_ROOT", str(tmp_path))

    light = presets.get("lecture", variant="light")
    dark = presets.get("lecture", variant="dark")

    assert light.palette.background == "#FFFFFF"
    assert light.palette.accent == "#0055AA"
    assert dark.palette.background == "#000000"
    assert dark.palette.accent == "#FFD166"
