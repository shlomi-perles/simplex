"""GhostSlideFade construction: default + explicit run_time."""

import pytest

pytest.importorskip("manim")

from manim import Square

from simplex.engine.ghost_fade import GhostSlideFade


def test_ghost_slide_fade_default_run_time_sums_phases() -> None:
    sq = Square()
    anim = GhostSlideFade(sq, fade_in_time=0.5, lifetime=2.0, fade_out_time=1.5)
    assert anim.run_time == pytest.approx(4.0)


def test_ghost_slide_fade_explicit_run_time_overrides_default() -> None:
    sq = Square()
    anim = GhostSlideFade(sq, lifetime=2.0, run_time=10.0)
    assert anim.run_time == pytest.approx(10.0)
