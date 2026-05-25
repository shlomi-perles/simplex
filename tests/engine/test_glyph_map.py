"""TransformByGlyphMap helpers -- delay rate-func shifter."""

import pytest

pytest.importorskip("manim")

from simplex.engine.glyph_map import _interpret_delay


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
    assert rf(0.0) == 0.0
    assert rf(0.2) == 0.0
    assert rf(1.0) == pytest.approx(1.0)
