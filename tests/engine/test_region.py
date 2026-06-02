"""Region geometry: full_frame, shrink, anchor math, reset, split."""

import numpy as np
import pytest

pytest.importorskip("manim")

from manim import DEFAULT_MOBJECT_TO_EDGE_BUFFER, DOWN, DR, LEFT, ORIGIN, RIGHT, UL, UP, UR
from manim.mobject.opengl.opengl_mobject import OpenGLMobject

from simplex.engine.region import Region


def _opengl_box(*, left: float, right: float, bottom: float, top: float) -> OpenGLMobject:
    mob = OpenGLMobject()
    mob.set_points(
        np.array(
            [
                [left, bottom, 0.0],
                [right, bottom, 0.0],
                [right, top, 0.0],
                [left, top, 0.0],
            ],
            dtype=float,
        )
    )
    return mob


def test_full_frame_center_is_origin() -> None:
    r = Region.full_frame()
    assert tuple(r.get_center()) == (0.0, 0.0, 0.0)


def test_region_is_a_transparent_manim_rectangle() -> None:
    from manim import Rectangle

    r = Region(top=2.0, bottom=-2.0, left=-3.0, right=3.0)
    assert isinstance(r, Rectangle)
    assert r.get_stroke_opacity() == pytest.approx(0.0)
    assert r.get_fill_opacity() == pytest.approx(0.0)


def test_shrink_top_moves_center_down() -> None:
    r = Region.full_frame()
    original_top = r.top
    r.shrink(top=1.0)
    assert r.top == pytest.approx(original_top - 1.0)
    assert r.get_center()[1] < 0.0


def test_update_keeps_float_behavior() -> None:
    r = Region(top=2.0, bottom=-2.0, left=-3.0, right=3.0)
    r.update(top=1.5, bottom=-1.5, left=-2.5, right=2.5)
    assert (r.top, r.bottom, r.left, r.right) == (1.5, -1.5, -2.5, 2.5)


def test_update_extracts_relevant_axis_from_points() -> None:
    r = Region(top=2.0, bottom=-2.0, left=-3.0, right=3.0)
    r.update(
        top=np.array([99.0, 1.5, 0.0]),
        bottom=np.array([99.0, -1.5, 0.0]),
        left=np.array([-2.5, 99.0, 0.0]),
        right=np.array([2.5, 99.0, 0.0]),
    )
    assert (r.top, r.bottom, r.left, r.right) == (1.5, -1.5, -2.5, 2.5)


def test_init_extracts_relevant_axis_from_points() -> None:
    r = Region(
        top=np.array([99.0, 1.5, 0.0]),
        bottom=np.array([99.0, -1.5, 0.0]),
        left=np.array([-2.5, 99.0, 0.0]),
        right=np.array([2.5, 99.0, 0.0]),
    )
    assert (r.top, r.bottom, r.left, r.right) == (1.5, -1.5, -2.5, 2.5)


def test_update_uses_mobject_inner_edges() -> None:
    from manim import Square

    top_ref = Square(side_length=2.0).move_to(np.array([0.0, 5.0, 0.0]))
    bottom_ref = Square(side_length=2.0).move_to(np.array([0.0, -5.0, 0.0]))
    left_ref = Square(side_length=2.0).move_to(np.array([-5.0, 0.0, 0.0]))
    right_ref = Square(side_length=2.0).move_to(np.array([5.0, 0.0, 0.0]))

    r = Region(top=2.0, bottom=-2.0, left=-3.0, right=3.0)
    r.update(top=top_ref, bottom=bottom_ref, left=left_ref, right=right_ref)

    assert r.top == pytest.approx(top_ref.get_bottom()[1])
    assert r.bottom == pytest.approx(bottom_ref.get_top()[1])
    assert r.left == pytest.approx(left_ref.get_right()[0])
    assert r.right == pytest.approx(right_ref.get_left()[0])


def test_update_uses_opengl_mobject_inner_edges() -> None:
    top_ref = _opengl_box(left=-1.0, right=1.0, bottom=4.0, top=6.0)
    bottom_ref = _opengl_box(left=-1.0, right=1.0, bottom=-6.0, top=-4.0)
    left_ref = _opengl_box(left=-6.0, right=-4.0, bottom=-1.0, top=1.0)
    right_ref = _opengl_box(left=4.0, right=6.0, bottom=-1.0, top=1.0)

    r = Region(top=2.0, bottom=-2.0, left=-3.0, right=3.0)
    r.update(top=top_ref, bottom=bottom_ref, left=left_ref, right=right_ref)

    assert r.top == pytest.approx(top_ref.get_bottom()[1])
    assert r.bottom == pytest.approx(bottom_ref.get_top()[1])
    assert r.left == pytest.approx(left_ref.get_right()[0])
    assert r.right == pytest.approx(right_ref.get_left()[0])


def test_init_uses_mobject_inner_edges() -> None:
    from manim import Square

    top_ref = Square(side_length=2.0).move_to(np.array([0.0, 5.0, 0.0]))
    bottom_ref = Square(side_length=2.0).move_to(np.array([0.0, -5.0, 0.0]))
    left_ref = Square(side_length=2.0).move_to(np.array([-5.0, 0.0, 0.0]))
    right_ref = Square(side_length=2.0).move_to(np.array([5.0, 0.0, 0.0]))

    r = Region(top=top_ref, bottom=bottom_ref, left=left_ref, right=right_ref)

    assert r.top == pytest.approx(top_ref.get_bottom()[1])
    assert r.bottom == pytest.approx(bottom_ref.get_top()[1])
    assert r.left == pytest.approx(left_ref.get_right()[0])
    assert r.right == pytest.approx(right_ref.get_left()[0])


def test_update_rejects_non_3d_point() -> None:
    r = Region(top=2.0, bottom=-2.0, left=-3.0, right=3.0)
    with pytest.raises(ValueError, match="3D point"):
        r.update(top=np.array([1.0, 2.0]))


def test_init_rejects_non_3d_point() -> None:
    with pytest.raises(ValueError, match="3D point"):
        Region(top=np.array([1.0, 2.0]), bottom=-2.0, left=-3.0, right=3.0)


def test_reset_restores_full_frame() -> None:
    r = Region.full_frame()
    r.shrink(top=1.0, bottom=0.5, left=0.25, right=0.25)
    r.reset()
    full = Region.full_frame()
    assert (r.top, r.bottom, r.left, r.right) == pytest.approx(
        (full.top, full.bottom, full.left, full.right)
    )


def test_anchor_point_for_each_direction() -> None:
    """Each cardinal direction maps to the corresponding region edge/corner."""
    r = Region(top=2.0, bottom=-2.0, left=-3.0, right=3.0)
    cases = {
        tuple(ORIGIN.tolist()): (0.0, 0.0),
        tuple(UP.tolist()): (0.0, 2.0),
        tuple(DOWN.tolist()): (0.0, -2.0),
        tuple(LEFT.tolist()): (-3.0, 0.0),
        tuple(RIGHT.tolist()): (3.0, 0.0),
        tuple(UL.tolist()): (-3.0, 2.0),
        tuple(UR.tolist()): (3.0, 2.0),
        tuple(DR.tolist()): (3.0, -2.0),
    }
    for direction, expected in cases.items():
        point = r._anchor_point(np.array(direction))
        assert (point[0], point[1]) == expected, f"direction {direction} wrong"


def test_place_with_buff_pulls_mob_inward() -> None:
    """A non-zero buff plus the mob's half-extent keeps the mob inside."""
    from manim import Dot

    r = Region.full_frame()
    dot = Dot(radius=0.1)
    r.place(dot, UP, buff=0.25)
    # Dot's top edge should be 0.25 below the region's top edge.
    assert dot.get_top()[1] == pytest.approx(r.top - 0.25)


def test_place_default_buff_uses_manim_edge_buffer() -> None:
    from manim import Dot

    r = Region.full_frame()
    dot = Dot(radius=0.1)

    r.place(dot, UP)

    assert dot.get_top()[1] == pytest.approx(r.top - DEFAULT_MOBJECT_TO_EDGE_BUFFER)


def test_place_corner_uses_mobject_aligned_edge() -> None:
    from manim import Square

    r = Region(top=2.0, bottom=-2.0, left=-3.0, right=3.0)
    sq = Square(side_length=1.0)
    r.place(sq, UR, buff=0.25)

    assert sq.get_right()[0] == pytest.approx(r.right - 0.25)
    assert sq.get_top()[1] == pytest.approx(r.top - 0.25)


def test_place_opengl_mobject_with_buff_pulls_inward() -> None:
    r = Region(top=2.0, bottom=-2.0, left=-3.0, right=3.0)
    mob = _opengl_box(left=-0.5, right=0.5, bottom=-0.5, top=0.5)

    r.place(mob, UR, buff=0.25)

    assert mob.get_right()[0] == pytest.approx(r.right - 0.25)
    assert mob.get_top()[1] == pytest.approx(r.top - 0.25)


def test_always_place_attaches_updater_to_placed_mobject() -> None:
    from manim import Square

    r = Region(top=2.0, bottom=-2.0, left=-3.0, right=3.0)
    sq = Square(side_length=1.0)

    r.always.place(sq, UR, buff=0.25)

    assert len(r.get_updaters()) == 0
    assert len(sq.get_updaters()) == 1
    assert sq.get_right()[0] == pytest.approx(r.right - 0.25)
    assert sq.get_top()[1] == pytest.approx(r.top - 0.25)


def test_always_place_updates_while_region_updating_is_suspended() -> None:
    from manim import Square

    r = Region(top=2.0, bottom=-2.0, left=-3.0, right=3.0)
    sq = Square(side_length=1.0)
    r.always.place(sq, UR, buff=0.25)
    initial_right = sq.get_right()[0]

    r.suspend_updating()
    r.shrink(left=1.0, right=1.0)
    sq.update(0)

    assert initial_right != pytest.approx(sq.get_right()[0])
    assert sq.get_right()[0] == pytest.approx(r.right - 0.25)
    assert sq.get_top()[1] == pytest.approx(r.top - 0.25)


def test_place_rejects_string_anchor() -> None:
    """Region directions are vectors now; strings raise instead of silently
    routing to the legacy match-case path."""
    from manim import Dot

    r = Region.full_frame()
    with pytest.raises((ValueError, TypeError)):
        r.place(Dot(), "top", buff=0.0)  # type: ignore[arg-type]


def test_split_right_returns_left_to_right_pieces() -> None:
    r = Region(top=2.0, bottom=-2.0, left=-3.0, right=3.0)
    pieces = r.split_regions(RIGHT, 3)
    assert len(pieces) == 3
    assert [(p.left, p.right) for p in pieces] == [(-3.0, -1.0), (-1.0, 1.0), (1.0, 3.0)]
    for p in pieces:
        assert p.top == 2.0
        assert p.bottom == -2.0


def test_split_left_returns_right_to_left_pieces() -> None:
    r = Region(top=2.0, bottom=-2.0, left=-3.0, right=3.0)
    pieces = r.split_regions(LEFT, 3)
    assert [(p.left, p.right) for p in pieces] == [(1.0, 3.0), (-1.0, 1.0), (-3.0, -1.0)]


def test_split_up_returns_bottom_to_top_pieces() -> None:
    r = Region(top=2.0, bottom=-2.0, left=-3.0, right=3.0)
    pieces = r.split_regions(UP, 4)
    assert len(pieces) == 4
    heights = [p.height for p in pieces]
    for h in heights:
        assert h == pytest.approx(1.0)
    # bottom-first ordering
    assert pieces[0].bottom == pytest.approx(-2.0)
    assert pieces[-1].top == pytest.approx(2.0)


def test_split_pieces_union_equals_original() -> None:
    r = Region(top=2.0, bottom=-2.0, left=-3.0, right=3.0)
    for axis, k in [(RIGHT, 5), (UP, 4), (DOWN, 2), (LEFT, 3)]:
        pieces = r.split_regions(axis, k)
        total_extent = sum(p.width for p in pieces)
        # Width sums to original along horizontal split; height along vertical.
        if axis[0] != 0:
            assert total_extent == pytest.approx(r.width)
        else:
            total_h = sum(p.height for p in pieces)
            assert total_h == pytest.approx(r.height)


def test_split_k_one_returns_copy() -> None:
    r = Region(top=2.0, bottom=-2.0, left=-3.0, right=3.0)
    pieces = r.split_regions(RIGHT, 1)
    assert len(pieces) == 1
    p = pieces[0]
    assert (p.top, p.bottom, p.left, p.right) == (r.top, r.bottom, r.left, r.right)


def test_linspace_right_defaults_to_interior_centers() -> None:
    r = Region(top=3.0, bottom=0.0, left=0.0, right=4.0)
    pts = r.linspace(RIGHT, 3)
    assert [tuple(p[:2]) for p in pts] == [(1.0, 1.5), (2.0, 1.5), (3.0, 1.5)]
    gaps = np.diff([r.left, *[p[0] for p in pts], r.right])
    assert list(gaps) == pytest.approx([1.0, 1.0, 1.0, 1.0])


def test_linspace_left_reverses_order() -> None:
    r = Region(top=3.0, bottom=0.0, left=0.0, right=4.0)
    pts = r.linspace(LEFT, 3)
    assert [p[0] for p in pts] == [3.0, 2.0, 1.0]


def test_linspace_include_edges_returns_endpoints() -> None:
    r = Region(top=2.0, bottom=-2.0, left=-3.0, right=3.0)
    pts = r.linspace(RIGHT, 3, include_edges=True)
    assert [p[0] for p in pts] == [-3.0, 0.0, 3.0]


def test_split_rejects_non_cardinal_axis() -> None:
    r = Region.full_frame()
    with pytest.raises(ValueError, match="cardinal direction"):
        r.split_regions(UR, 3)


def test_split_rejects_k_zero() -> None:
    r = Region.full_frame()
    with pytest.raises(ValueError, match=r"k must be >= 1"):
        r.split_regions(RIGHT, 0)
