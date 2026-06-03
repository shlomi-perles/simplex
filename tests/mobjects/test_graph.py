"""Smoke construction tests for the Node / Edge mobjects."""

import pytest

pytest.importorskip("manim")

import numpy as np
from numpy.testing import assert_allclose

from simplex.mobjects.graph import Edge, Node


def test_node_constructs_with_label() -> None:
    n = Node(label="A")
    # Two children: the circle and the label.
    assert len(n.submobjects) == 2


def test_node_registers_shrink_exit_animation() -> None:
    from manim import ShrinkToCenter

    from simplex.engine.animations import exit_for

    n = Node(label="X")
    anim = exit_for(n)
    assert isinstance(anim, ShrinkToCenter)


def test_edge_between_points_has_a_line() -> None:
    from manim import Line

    e = Edge(np.array([0.0, 0.0, 0.0]), np.array([1.0, 0.0, 0.0]))
    assert isinstance(e, Line)
    assert_allclose(e.get_start(), np.array([0.0, 0.0, 0.0]))
    assert_allclose(e.get_end(), np.array([1.0, 0.0, 0.0]))


def test_edge_between_mobjects_uses_boundary_points() -> None:
    from manim import LEFT, RIGHT, Circle

    start = Circle(radius=1).shift(2 * LEFT)
    end = Circle(radius=1).shift(2 * RIGHT)
    e = Edge(start, end)

    assert_allclose(e.get_start(), np.array([-1.0, 0.0, 0.0]), atol=1e-7)
    assert_allclose(e.get_end(), np.array([1.0, 0.0, 0.0]), atol=1e-7)


def test_edge_with_weight_adds_label() -> None:
    e = Edge(np.array([0.0, 0.0, 0.0]), np.array([1.0, 0.0, 0.0]), weight="3")
    assert len(e.submobjects) == 1
    assert e.submobjects[0].get_center()[0] == pytest.approx(0.5)
