"""Region geometry: full_frame, shrink, anchor math, reset."""

import pytest

pytest.importorskip("manim")

from simplex.engine.region import Region


def test_full_frame_center_is_origin() -> None:
    r = Region.full_frame()
    assert tuple(r.center) == (0.0, 0.0, 0.0)


def test_shrink_top_moves_center_down() -> None:
    r = Region.full_frame()
    original_top = r.top
    r.shrink(top=1.0)
    assert r.top == pytest.approx(original_top - 1.0)
    assert r.center[1] < 0.0


def test_reset_restores_full_frame() -> None:
    r = Region.full_frame()
    r.shrink(top=1.0, bottom=0.5, left=0.25, right=0.25)
    r.reset()
    full = Region.full_frame()
    assert (r.top, r.bottom, r.left, r.right) == (full.top, full.bottom, full.left, full.right)
