"""Showcase deck -- exercises every Simplex-specific helper end-to-end.

Each scene targets one module so a reader can correlate the output with the
source.
"""

import math

import numpy as np
from manim import (
    BLUE,
    DOWN,
    GOLD,
    GREEN,
    LEFT,
    PI,
    RED,
    RIGHT,
    UP,
    Arrow,
    Circle,
    Dot,
    FadeIn,
    Line,
    MathTex,
    ShrinkToCenter,
    VGroup,
    Write,
    always_redraw,
)

from simplex.engine.animations import set_exit_animation
from simplex.engine.code import code_block, code_explain, highlight_code_lines
from simplex.engine.debug import bounding_box, indexx_labels
from simplex.engine.dynamics import DN, VT
from simplex.engine.geometry import (
    SurroundingRectangleUnion,
    Vcis,
    get_convex_hull_polygon,
    get_surrounding_rectangle,
)
from simplex.engine.text import BodyText, Caption, Definition, color_tex
from simplex.engine.transforms import GhostSlideFade, TransformByGlyphMap
from simplex.slides import ContentSlide
from simplex.slides.components import ArrayMob, ArrayPointer, Edge, Node


class TextHelpers(ContentSlide):
    header = "engine/text.py -- BodyText, Caption, Definition, color\\_tex"
    page_number = 1

    def construct(self) -> None:
        body = BodyText(r"Body paragraphs default to \textit{theme.typography.body}: $E = mc^2$.")
        self.region.place(body, "top", buff=0.3)
        self.add(body)
        self.next_slide()

        cap = Caption("Captions use the smaller theme.typography.caption font size.")
        cap.next_to(body, DOWN, buff=0.4)
        self.play(Write(cap))
        self.next_slide()

        defn = Definition(
            r"\textbf{Definition.} A graph is a pair $(V, E)$ where $V$ is a vertex set "
            r"and $E \subseteq V \times V$ a set of edges. Definition wraps content in the "
            r"theme's \texttt{definition} environment so long prose stays inside a fixed width."
        )
        defn.next_to(cap, DOWN, buff=0.4)
        self.play(Write(defn))
        self.next_slide()

        formula = MathTex(r"a^2 + b^2 = c^2")
        formula.next_to(defn, DOWN, buff=0.4)
        color_tex(formula, {"a": "#FF6B6B", "b": "#4ECDC4", "c": "#FFD93D"}, tex_class=MathTex)
        self.play(Write(formula))
        self.next_slide()


class CodeHelpers(ContentSlide):
    header = "engine/code.py -- code\\_block + highlight + explain"
    page_number = 2

    def construct(self) -> None:
        snippet = (
            "def bfs(graph, start):\n"
            "    queue = [start]\n"
            "    visited = {start}\n"
            "    while queue:\n"
            "        node = queue.pop(0)\n"
            "        for nb in graph[node]:\n"
            "            if nb not in visited:\n"
            "                visited.add(nb)\n"
            "                queue.append(nb)\n"
            "    return visited\n"
        )
        code = code_block(snippet, language="python")
        code.scale_to_fit_width(self.region.width * 0.8)
        self.region.place(code, "top", buff=0.3)
        self.play(FadeIn(code))
        self.next_slide()

        fade, indicate = highlight_code_lines(code, lines=[5, 6, 7, 8, 9])
        self.play(fade)
        self.play(indicate)
        self.next_slide()

        mob, anim = code_explain(
            code,
            lines=[5, 6],
            explanation="Dequeue + expand neighbours",
        )
        self.add(mob)
        self.play(anim)
        self.next_slide()


class GraphAndArray(ContentSlide):
    header = "Components -- Node, Edge, ArrayMob, ArrayPointer"
    page_number = 3

    def construct(self) -> None:
        n1 = Node("1")
        n2 = Node("2")
        n3 = Node("3")
        n1.move_to(LEFT * 2 + UP * 1.2)
        n2.move_to(RIGHT * 2 + UP * 1.2)
        n3.move_to(UP * 2.4)
        edges = [
            Edge(n1, n2, weight="3"),
            Edge(n1, n3, weight="1"),
            Edge(n2, n3, weight="2"),
        ]
        self.play(FadeIn(n1, n2, n3, *edges))
        self.next_slide()

        arr = ArrayMob(
            "A:",
            "-",
            "8",
            "1",
            "3",
            "9",
            show_indices=True,
            starting_index=1,
            name_scale=0.18,
        )
        arr.scale(0.8)
        self.region.place(arr, "bottom", buff=0.6)
        self.play(Write(arr))
        self.next_slide()

        self.play(arr.animate.at(1, "b"))
        self.play(arr.indicate_at(2))
        self.play(arr.push("5"))
        self.play(arr.swap(2, 4))
        self.next_slide()

        pointer = ArrayPointer(arr, 2, text="here")
        self.play(Write(pointer))
        self.play(pointer.to_entry(4))
        self.next_slide()


class RegionAnchors(ContentSlide):
    header = "engine/region.py -- anchors + shrink"
    page_number = 4

    def construct(self) -> None:
        markers = []
        for anchor in (
            "top-left",
            "top-right",
            "bottom-left",
            "bottom-right",
            "center",
        ):
            mob = Caption(anchor)
            self.region.place(mob, anchor, buff=0.25)
            markers.append(mob)
        self.play(*(Write(m) for m in markers))
        self.next_slide()

        self.region.shrink(left=2.5, right=2.5)
        sidebar = Caption("shrink(left=2.5, right=2.5) reflows subsequent placements")
        self.region.place(sidebar, "center")
        self.play(Write(sidebar))
        self.next_slide()

        self.region.reset()
        full = Caption("region.reset() restores the full frame")
        self.region.place(full, "center")
        self.play(Write(full))
        self.next_slide()


class ExitAnimations(ContentSlide):
    header = "Remove + set\\_exit\\_animation + clear\\_scene"
    page_number = 5

    def construct(self) -> None:
        keep = BodyText("survives via clear\\_scene(exclude=[this])")
        fade = BodyText("default exit: FadeOut")
        shrink = BodyText("custom exit via set\\_exit\\_animation(mob, ShrinkToCenter)")
        set_exit_animation(shrink, ShrinkToCenter)

        keep.shift(UP * 1.8)
        shrink.shift(DOWN * 1.8)
        self.add(keep, fade, shrink)
        self.next_slide()

        self.clear_scene(exclude=[keep])
        self.next_slide()


class GeometryHelpers(ContentSlide):
    header = "engine/geometry.py -- convex hull + surrounding rect"
    page_number = 6

    def construct(self) -> None:
        points = np.array(
            [
                [-2.0, -1.0, 0.0],
                [2.0, -1.0, 0.0],
                [-1.0, 1.2, 0.0],
                [1.0, 1.2, 0.0],
                [0.0, 0.0, 0.0],
                [-1.5, 0.3, 0.0],
                [1.5, 0.3, 0.0],
            ],
        )
        dots = [Dot(p) for p in points]
        self.play(*(FadeIn(d) for d in dots))

        hull = get_convex_hull_polygon(points, round_radius=0.15)
        hull.set_stroke(width=4)
        self.play(Write(hull))
        self.next_slide()

        a = Dot(LEFT * 3 + DOWN)
        b = Dot(RIGHT * 3 + UP)
        rect = get_surrounding_rectangle(a, b, buff=0.3)
        self.play(FadeIn(a, b), Write(rect))
        self.next_slide()


class GlyphMapTransform(ContentSlide):
    header = "engine/transforms.py -- TransformByGlyphMap"
    page_number = 7

    def construct(self) -> None:
        eq1 = MathTex("f(x) = 4x^2 + 5x + 6").scale(1.4)
        eq2 = MathTex("f(-3) = 4(-3)^2 + 5(-3) + 6").scale(1.4)
        self.region.place(eq1, "center")
        eq2.move_to(eq1)
        self.add(eq1)
        self.next_slide()

        # Map every "x" -> "(-3)" group; the unmentioned glyphs slide into place.
        self.play(
            TransformByGlyphMap(
                eq1,
                eq2,
                ([2], [2, 3, 4]),
                ([6], [7, 8, 9, 10, 11]),
                ([10], [15, 16, 17, 18, 19]),
                run_time=2.0,
            )
        )
        self.next_slide()

        # Per-entry kwargs: path_arc + delay + a custom shift on the introducer.
        eq3 = MathTex("f(-3) = 4 \\cdot 9 + 5(-3) + 6").scale(1.4).move_to(eq2)
        self.play(
            TransformByGlyphMap(
                eq2,
                eq3,
                ([7, 8, 9, 10, 11, 12], [7, 8, 9], {"path_arc": PI / 2}),
                ([], [10], {"delay": 0.4}),
                run_time=2.0,
            )
        )
        self.next_slide()


class TrackingHelpers(ContentSlide):
    header = "engine/dynamics.py -- VT, DN + engine/geometry.py Vcis"
    page_number = 8

    def construct(self) -> None:
        # A clock-style pointer driven by a VT angle.
        angle = VT(0.0)
        face = Circle(radius=2.0, color=BLUE).set_stroke(width=2)
        ticks = VGroup(
            *(
                Line(2.0 * Vcis(k * PI / 6), 1.85 * Vcis(k * PI / 6), stroke_width=2)
                for k in range(12)
            )
        )
        hand = always_redraw(
            lambda: Arrow(
                start=face.get_center(),
                end=face.get_center() + 1.7 * Vcis(~angle),
                buff=0.0,
                color=GOLD,
            )
        )
        readout = DN(
            lambda: math.degrees(~angle) % 360,
            num_decimal_places=0,
            unit=r"^{\circ}",
        )
        readout.scale(0.9).next_to(face, DOWN, buff=0.5)
        self.region.place(face, "center")
        self.add(face, ticks, hand, readout)
        self.next_slide()

        # `~vt` reads it; `vt @ x` returns an animate.set_value builder for play().
        self.play(angle @ (PI / 2), run_time=1.5)
        self.next_slide()
        self.play(angle @ (5 * PI / 6), run_time=1.5)
        self.next_slide()
        self.play(angle @ (-PI / 4), run_time=1.5)
        self.next_slide()


class ShapeAndDebug(ContentSlide):
    header = "engine/geometry.py SurroundingRectangleUnion + engine/debug.py"
    page_number = 9

    def construct(self) -> None:
        # 6x4 grid of dots; group three subsets and surround each with a single
        # merged polygon (the rectangles for adjacent dots union together).
        grid = VGroup(
            *(
                Dot(point=np.array([col - 2.5, row - 1.5, 0.0]) * 0.55, radius=0.12)
                for row in range(4)
                for col in range(6)
            )
        )
        grid.set_color(GOLD)
        groups = (
            ([0, 1, 6, 7], RED),
            ([3, 4, 5, 9, 10, 11], GREEN),
            ([12, 13, 18, 19, 20, 21], BLUE),
        )
        unions = VGroup(
            *(
                SurroundingRectangleUnion(
                    *(grid[i] for i in indices),
                    buff=0.18,
                    unbuff=0.06,
                    corner_radius=0.12,
                    stroke_color=color,
                )
                for indices, color in groups
            )
        )
        self.region.place(grid, "center")
        unions.move_to(grid)
        self.play(FadeIn(grid))
        self.play(*(Write(u) for u in unions))
        self.next_slide()

        # Multi-color index labels for a multi-string MathTex.
        eq = MathTex(r"\sin\!\left(", r"{a^2 + b^2}", r"\over", r"{3n + 1}", r"\right)")
        eq.scale(1.2).next_to(grid, DOWN, buff=0.6)
        labels = indexx_labels(eq)
        self.play(FadeIn(eq), FadeIn(labels))
        self.next_slide()

        # bounding_box(always=True) tracks an animated mob.
        target = MathTex(r"\Box").scale(1.5).move_to(LEFT * 4 + UP * 2)
        bb = bounding_box(target, always=True, include_center=True)
        self.add(target, bb)
        self.play(target.animate.shift(RIGHT * 2 + DOWN * 1.5).rotate(PI / 6), run_time=1.5)
        self.next_slide()

        # GhostSlideFade: drift+fade cue that cleans itself up.
        ghost = MathTex(r"\swarrow").scale(1.6).move_to(grid.get_corner(UP + RIGHT))
        self.play(GhostSlideFade(ghost, shift_vector=DOWN + LEFT, lifetime=1.5))
        self.next_slide()
