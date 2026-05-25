"""VT operator sugar + DN auto-tracking + keep_orientation marker setup."""

import pytest

pytest.importorskip("manim")

from simplex.engine.dynamics import VT


def test_vt_invert_reads_value() -> None:
    v = VT(3.5)
    assert ~v == pytest.approx(3.5)


def test_vt_imatmul_sets_value_in_place() -> None:
    v = VT(0.0)
    v @= 7.5
    assert v.get_value() == pytest.approx(7.5)


def test_vt_matmul_returns_animate_set_value() -> None:
    v = VT(1.0)
    builder = v @ 9.0
    # `animate.set_value(9)` returns the same _AnimationBuilder back
    assert builder is not None
    assert hasattr(builder, "build")


def test_vt_inherits_valuetracker_arithmetic() -> None:
    # ValueTracker already overloads += etc. in 0.19+; VT must keep that working.
    v = VT(2.0)
    v += 3.0
    assert v.get_value() == pytest.approx(5.0)
