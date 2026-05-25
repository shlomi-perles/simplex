"""Smoke construction tests for the Node / Edge mobjects."""

import pytest

pytest.importorskip("manim")

import numpy as np

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
    e = Edge(np.array([0.0, 0.0, 0.0]), np.array([1.0, 0.0, 0.0]))
    assert len(e.submobjects) >= 1


def test_edge_with_weight_adds_label() -> None:
    e = Edge(np.array([0.0, 0.0, 0.0]), np.array([1.0, 0.0, 0.0]), weight="3")
    assert len(e.submobjects) == 2
