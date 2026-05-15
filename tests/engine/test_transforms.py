"""TransformByGlyphMap + GhostSlideFade construction smoke tests.

Full glyph mapping needs a LaTeX render; here we check object construction,
default-runtime math, and the rate-func delay shifter.
"""

import pytest

pytest.importorskip("manim")

from manim import Square

from simplex.engine.transforms import GhostSlideFade, _interpret_delay


def test_ghost_slide_fade_default_run_time_sums_phases() -> None:
    sq = Square()
    anim = GhostSlideFade(sq, fade_in_time=0.5, lifetime=2.0, fade_out_time=1.5)
    assert anim.run_time == pytest.approx(4.0)


def test_ghost_slide_fade_explicit_run_time_overrides_default() -> None:
    sq = Square()
    anim = GhostSlideFade(sq, lifetime=2.0, run_time=10.0)
    assert anim.run_time == pytest.approx(10.0)


def test_interpret_delay_zero_is_noop() -> None:
    opts = {"run_time": 1.0}
    out = _interpret_delay(opts)
    assert "rate_func" not in out
    assert out["run_time"] == 1.0


def test_interpret_delay_stretches_run_time_and_holds_at_zero() -> None:
    opts = {"run_time": 1.0, "delay": 0.5}
    out = _interpret_delay(opts)
    assert out["run_time"] == pytest.approx(1.5)
    rf = out["rate_func"]
    # During the delay window the curve stays at 0.
    assert rf(0.0) == 0.0
    assert rf(0.2) == 0.0
    # After the delay the curve advances and finishes at 1.
    assert rf(1.0) == pytest.approx(1.0)
