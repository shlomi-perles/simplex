"""Darcula registration is idempotent and visible to Pygments."""

import pytest

pytest.importorskip("pygments")

from simplex.engine.code import DarculaStyle, register_darcula


def test_register_darcula_adds_to_style_map() -> None:
    import pygments.styles

    register_darcula()
    assert "darcula" in pygments.styles.STYLE_MAP


def test_register_darcula_is_idempotent() -> None:
    register_darcula()
    register_darcula()
    register_darcula()


def test_darcula_style_has_expected_background() -> None:
    assert DarculaStyle.background_color == "#111111"
