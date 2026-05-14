"""Showcase deck -- exercises every Simplex-specific helper end-to-end.

Each scene targets one module so a reader can correlate the output with the
source.
"""

import numpy as np
from manim import (
    DOWN,
    LEFT,
    RIGHT,
    UP,
    Dot,
    FadeIn,
    MathTex,
    ShrinkToCenter,
    Write,
)

from simplex.engine.animations import set_exit_animation
from simplex.engine.code import code_block, code_explain, highlight_code_lines
from simplex.engine.geometry import (
    get_convex_hull_polygon,
    get_surrounding_rectangle,
)
from simplex.engine.text import BodyText, Caption, Definition, color_tex
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
        color_tex(formula, {"a": "#FF6B6B", "b": "#4ECDC4", "c": "#FFD93D"})
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
