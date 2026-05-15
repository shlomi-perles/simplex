"""Multi-axis scale_to_fit + stroke-aware scale."""

import pytest

pytest.importorskip("manim")

from manim import Square

from simplex.engine.scaling import scale_to_fit, scale_with_stroke_width


def test_scale_to_fit_x_only() -> None:
    sq = Square(side_length=2.0)
    scale_to_fit(sq, len_x=4.0)
    assert sq.width == pytest.approx(4.0)
    # Aspect preserved -> height also doubled.
    assert sq.height == pytest.approx(4.0)


def test_scale_to_fit_smallest_factor_wins() -> None:
    sq = Square(side_length=2.0)
    # len_x suggests x2, len_y suggests x0.5 -> the smaller wins, fits inside both.
    scale_to_fit(sq, len_x=4.0, len_y=1.0)
    assert sq.width == pytest.approx(1.0)


def test_scale_to_fit_buff_subtracts_from_target() -> None:
    sq = Square(side_length=2.0)
    scale_to_fit(sq, len_x=4.0, buff=0.5)
    # (4 - 2*0.5) / 2 = 1.5 -> width ~3
    assert sq.width == pytest.approx(3.0)


def test_scale_with_stroke_width_doubles_stroke() -> None:
    sq = Square(side_length=1.0)
    initial_stroke = sq.get_stroke_width()
    scale_with_stroke_width(sq, 2.0)
    assert sq.get_stroke_width() == pytest.approx(initial_stroke * 2.0)
