"""Manim palette registry and custom palette loading."""

import json
import plistlib
from pathlib import Path

import pytest

from simplex.theme.palettes import (
    MANIM_DEFAULT,
    SIMPLEX_LIGHT,
    available_palette_names,
    resolve_palette,
    semantic_palette_for,
    studio_palette_data,
)


def test_resolves_manim_default_palette() -> None:
    palette = resolve_palette(MANIM_DEFAULT)

    assert palette.colors["BLUE"] == "#58C4DD"
    assert palette.colors["GRAY"] == "#888888"


def test_resolves_simplex_light_palette() -> None:
    palette = resolve_palette(SIMPLEX_LIGHT)

    assert palette.background == "#EEEAD8"
    assert palette.colors["BLUE"] == "#426A79"
    assert palette.colors["WHITE"] == "#3C313F"


def test_resolves_vendored_iterm_palette() -> None:
    palette = resolve_palette("Belafonte Day")

    assert palette.background == "#D5CCBA"
    assert palette.colors["BLUE"] == "#426A79"
    assert "Belafonte Day" in available_palette_names()


def test_custom_json_palette_wins_from_project_dir(tmp_path: Path) -> None:
    palette_dir = tmp_path / "simplex_themes" / "palette_styles"
    palette_dir.mkdir(parents=True)
    (palette_dir / "custom_light.json").write_text(
        json.dumps(
            {
                "background_color": "#FAFAFA",
                "manim_colors": {
                    "BLUE_C": "#123456",
                    "WHITE": "#111111",
                    "BLACK": "#FFFFFF",
                    "GOLD": "#BBAA00",
                    "YELLOW": "#CCAA00",
                    "GREEN": "#008800",
                    "ORANGE": "#CC5500",
                },
            }
        ),
        encoding="utf-8",
    )

    palette = resolve_palette("custom_light", repo_root=tmp_path)

    assert palette.background == "#FAFAFA"
    assert palette.colors["BLUE"] == "#123456"
    assert semantic_palette_for("custom_light", repo_root=tmp_path)["font"] == "#111111"


def test_custom_itermcolors_palette_loads(tmp_path: Path) -> None:
    palette_dir = tmp_path / "simplex_themes" / "palette_styles"
    palette_dir.mkdir(parents=True)
    data = {"Background Color": _rgb(16, 32, 48)}
    for index in range(16):
        data[f"Ansi {index} Color"] = _rgb(index * 10, index * 10 + 1, index * 10 + 2)
    with (palette_dir / "tiny.itermcolors").open("wb") as file:
        plistlib.dump(data, file)

    palette = resolve_palette("tiny", repo_root=tmp_path)

    assert palette.background == "#102030"
    assert palette.colors["BLUE"] == "#28292A"
    assert palette.colors["LIGHT_PINK"] == "#828384"


def test_studio_palette_data_includes_custom_names(tmp_path: Path) -> None:
    palette_dir = tmp_path / "simplex_themes" / "palette_styles"
    palette_dir.mkdir(parents=True)
    (palette_dir / "demo.json").write_text(
        json.dumps({"background_color": "#FFFFFF", "manim_colors": {"WHITE": "#000000"}}),
        encoding="utf-8",
    )

    data = studio_palette_data(repo_root=tmp_path)
    palette_list = data["PALETTE_LIST"]
    palette_custom = data["PALETTE_CUSTOM"]

    assert isinstance(palette_list, list)
    assert isinstance(palette_custom, list)
    assert "demo" in palette_list
    assert "demo" in palette_custom


def test_unknown_palette_raises_clear_error() -> None:
    with pytest.raises(KeyError, match="unknown Manim palette"):
        resolve_palette("missing-palette-name")


def _rgb(r: int, g: int, b: int) -> dict[str, float]:
    return {
        "Red Component": r / 255,
        "Green Component": g / 255,
        "Blue Component": b / 255,
    }
