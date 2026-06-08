"""Plugin palette application patches Manim constants before scenes import them."""

import json
from pathlib import Path

import manim
import manim.utils.color.manim_colors as manim_colors
import pytest

from simplex import plugin
from simplex.theme import presets
from simplex.theme.palettes import apply_manim_palette


def test_apply_manim_palette_patches_public_and_source_modules() -> None:
    try:
        apply_manim_palette(manim, presets.SIMPLEX_LIGHT)

        assert manim.BLUE.to_hex().upper() == "#426A79"
        assert manim.BLUE_A.to_hex().upper() == "#688894"
        assert manim_colors.BLUE.to_hex().upper() == "#426A79"
    finally:
        apply_manim_palette(manim, presets.SIMPLEX_DARK)


def test_activate_sets_background_from_resolved_theme(monkeypatch: pytest.MonkeyPatch) -> None:
    try:
        monkeypatch.setenv("SIMPLEX_THEME", "simplex_light")
        plugin.activate()

        assert manim.config.background_color.to_hex().upper() == "#EEEAD8"
        assert manim.BLUE.to_hex().upper() == "#426A79"
    finally:
        monkeypatch.setenv("SIMPLEX_THEME", "simplex_dark")
        plugin.activate()


def test_activate_resolves_custom_theme_from_project_root(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    theme_dir = tmp_path / "simplex_themes" / "themes"
    theme_dir.mkdir(parents=True)
    (theme_dir / "warm_light.json").write_text(
        json.dumps(
            {
                "manim_palette": "simplex_light",
                "palette": {"background": "#FDF6E3", "font": "#073642"},
            }
        ),
        encoding="utf-8",
    )

    try:
        monkeypatch.setenv("SIMPLEX_PROJECT_ROOT", str(tmp_path))
        monkeypatch.setenv("SIMPLEX_THEME", "warm_light")
        plugin.activate()

        assert manim.config.background_color.to_hex().upper() == "#FDF6E3"
        assert manim.BLUE.to_hex().upper() == "#426A79"
    finally:
        monkeypatch.setenv("SIMPLEX_THEME", "simplex_dark")
        plugin.activate()


def test_activate_passes_theme_variant_to_custom_theme(
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
                }
            }
        ),
        encoding="utf-8",
    )

    try:
        monkeypatch.setenv("SIMPLEX_PROJECT_ROOT", str(tmp_path))
        monkeypatch.setenv("SIMPLEX_THEME", "lecture")
        monkeypatch.setenv("SIMPLEX_THEME_VARIANT", "light")
        plugin.activate()

        assert manim.config.background_color.to_hex().upper() == "#FFFFFF"
    finally:
        monkeypatch.setenv("SIMPLEX_THEME", "simplex_dark")
        monkeypatch.delenv("SIMPLEX_THEME_VARIANT", raising=False)
        plugin.activate()
