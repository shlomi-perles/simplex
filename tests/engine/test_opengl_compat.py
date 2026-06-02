"""OpenGL/Cairo mobject compatibility helpers."""

import numpy as np
import pytest

pytest.importorskip("manim")

from manim import UR, Square, VGroup
from manim.mobject.opengl.opengl_mobject import OpenGLMobject

from simplex.engine.opengl_compat import critical_point, is_mobject, set_mobject_z_index


def _opengl_box() -> OpenGLMobject:
    mob = OpenGLMobject()
    mob.set_points(
        np.array(
            [
                [-1.0, -2.0, 0.0],
                [3.0, -2.0, 0.0],
                [3.0, 4.0, 0.0],
                [-1.0, 4.0, 0.0],
            ],
            dtype=float,
        )
    )
    return mob


def test_critical_point_accepts_cairo_mobject() -> None:
    square = Square(side_length=2.0)

    assert critical_point(square, UR)[:2] == pytest.approx((1.0, 1.0))


def test_critical_point_accepts_opengl_mobject() -> None:
    mob = _opengl_box()

    assert is_mobject(mob)
    assert critical_point(mob, UR)[:2] == pytest.approx((3.0, 4.0))


def test_set_mobject_z_index_uses_cairo_family() -> None:
    child = Square()
    group = VGroup(child)

    result = set_mobject_z_index(group, 7, family=True)

    assert result is group
    assert group.z_index == 7
    assert child.z_index == 7


def test_set_mobject_z_index_uses_opengl_family() -> None:
    child = OpenGLMobject()
    group = OpenGLMobject()
    group.add(child)

    result = set_mobject_z_index(group, 11, family=True)

    assert result is group
    assert group.z_index == 11
    assert child.z_index == 11
