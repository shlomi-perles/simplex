"""Showcase deck -- exercises every Simplex-specific helper end-to-end.

Each scene targets one module so a reader can correlate the output with the
source. Scenes call ``self.next_slide(name=...)`` to start a main slide and
bare ``self.next_slide()`` for sub-stops within it.

Slide chrome (page number, clock) used to be drawn into each frame via
``make_chrome(..., page=…)``; it now lives in the RevealJS host so the
showcase only renders **content** chrome (header / footer). Toggle the
clock or counter from ``[web]`` in ``deck.toml``.
"""

import math

import numpy as np
from manim import (
    BLUE,
    DL,
    DOWN,
    DR,
    GOLD,
    GREEN,
    LEFT,
    ORIGIN,
    PI,
    RED,
    RIGHT,
    UL,
    UP,
    UR,
    Arrow,
    Circle,
    Dot,
    FadeIn,
    Line,
    MathTex,
    ShrinkToCenter,
    Square,
    Tex,
    Triangle,
    Unwrite,
    VGroup,
    Write,
    always_redraw,
)

from simplex.engine.animations import register_exit, set_exit_animation
from simplex.engine.code import (
    code_block,
    code_explain,
    code_with_math,
    highlight_code_lines,
    transform_code_lines,
)
from simplex.engine.debug import bounding_box, indexx_labels
from simplex.engine.dynamics import DN, VT
from simplex.engine.geometry import (
    SurroundingRectangleUnion,
    Vcis,
    get_convex_hull_polygon,
    get_surrounding_rectangle,
)
from simplex.engine.ghost_fade import GhostSlideFade
from simplex.engine.glyph_map import TransformByGlyphMap
from simplex.engine.scaling import scale_to_fit
from simplex.engine.text import Caption, TexPage, color_tex
from simplex.mobjects import ArrayMob, ArrayPointer, Edge, Node
from simplex.slides import BaseSlide, OutlinePart, OutlineScene, make_chrome
from simplex.theme.context import get_active_theme


class TextHelpers(BaseSlide):
    def setup(self) -> None:
        super().setup()
        chrome = make_chrome(
            get_active_theme(),
            self.region,
            header=r"engine/text.py -- Tex, Caption, TexPage, color\_tex",
        )
        self.add_to_canvas(**chrome.mobjects)
        self.region = chrome.body_region

    def construct(self) -> None:
        body = Tex(r"Body paragraphs default to \textit{theme.typography.body}: $E = mc^2$.")
        self.region.place(body, UP, buff=0.3)
        self.add(body)
        self.next_slide(name="TextHelpers")

        cap = Caption("Captions use the smaller theme.typography.caption font size.")
        cap.next_to(body, DOWN, buff=0.4)
        self.play(Write(cap))
        self.next_slide()

        # TexPage wraps long prose in a fixed-width minipage. Default is 8cm
        # (matches the historical ``Definition``); pass ``width_cm`` per call.
        defn = TexPage(
            r"\textbf{TexPage.} A graph is a pair $(V, E)$ where $V$ is a vertex set "
            r"and $E \subseteq V \times V$ a set of edges. TexPage wraps content in a "
            r"\texttt{minipage} environment so long prose stays inside a fixed width "
            r"(default 8 cm; override per-instance with \texttt{width\_cm=...})."
        )
        defn.next_to(cap, DOWN, buff=0.4)
        self.play(Write(defn))
        self.next_slide()

        wide = TexPage(
            r"\textbf{Same prose, width\_cm=12.} Notice the wider column.",
            width_cm=12.0,
        )
        wide.next_to(defn, DOWN, buff=0.3)
        self.play(Write(wide))
        self.next_slide()

        formula = MathTex(r"a^2 + b^2 = c^2")
        formula.next_to(wide, DOWN, buff=0.4)
        color_tex(formula, {"a": "#FF6B6B", "b": "#4ECDC4", "c": "#FFD93D"}, tex_class=MathTex)
        self.play(Write(formula))
        self.next_slide()


class CodeHelpers(BaseSlide):
    def setup(self) -> None:
        super().setup()
        chrome = make_chrome(
            get_active_theme(),
            self.region,
            header=r"engine/code.py -- code\_block + highlight + explain + transform",
        )
        self.add_to_canvas(**chrome.mobjects)
        self.region = chrome.body_region

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
        self.region.place(code, UP, buff=0.3)
        self.play(FadeIn(code))
        self.next_slide(name="CodeHelpers")

        result = highlight_code_lines(code, lines=[5, 6, 7, 8, 9])
        self.play(result.fade)
        if result.indicate is not None:
            self.play(result.indicate)
        self.next_slide()

        mob, anim = code_explain(
            code,
            lines=[5, 6],
            explanation="Dequeue + expand neighbours",
        )
        self.add(mob)
        self.play(anim)
        self.next_slide()

        # transform_code_lines morphs one Code block into another by line
        # mapping. Here we show a refactored two-liner side-by-side.
        refactor_src = code_block(
            "for nb in graph[node]:\n    if nb not in visited:\n",
            language="python",
        )
        refactor_dst = code_block(
            "for nb in graph[node] - visited:\n    visited.add(nb)\n",
            language="python",
        )
        refactor_src.scale(0.6).next_to(code, DOWN, buff=0.4)
        refactor_dst.scale(0.6).move_to(refactor_src)
        self.play(FadeIn(refactor_src))
        self.play(transform_code_lines(refactor_src, refactor_dst, {1: 1, 2: 2}))
        self.next_slide()


class CodeWithMath(BaseSlide):
    def setup(self) -> None:
        super().setup()
        chrome = make_chrome(
            get_active_theme(),
            self.region,
            header=r"engine/code.py -- code\_with\_math (inline LaTeX in code)",
        )
        self.add_to_canvas(**chrome.mobjects)
        self.region = chrome.body_region

    def construct(self) -> None:
        # ``code_with_math`` renders any ``$...$`` regions as MathTex.
        # The inline math sits at the surrounding code's font size --
        # the helper calibrates against a cached reference glyph, so big
        # operators (``\bigcup``) and short symbols (``\infty``) both
        # land at the right size.
        pseudo = code_with_math(
            "def dijkstra(G, s):\n"
            "    for v in $V_G$:\n"
            "        d[v] = $\\infty$\n"
            "    d[s] = $0$\n"
            "    Q = $V_G$\n"
            "    while $Q \\neq \\emptyset$:\n"
            "        u = argmin($d[v] : v \\in Q$)\n"
            "        Q.remove(u)\n"
            "        for (u, v) in $E_G$:\n"
            "            if $d[v] > d[u] + w(u, v)$:\n"
            "                $d[v] \\gets d[u] + w(u, v)$\n",
            language="python",
        )
        pseudo.scale_to_fit_width(self.region.width * 0.85)
        self.region.place(pseudo, UP, buff=0.3)
        self.play(FadeIn(pseudo))
        self.next_slide(name="CodeWithMath")

        # All the engine/code helpers still work over math-laden blocks
        # -- highlight, explain, and transform all operate on
        # ``code_lines`` so the inline-tex substitutions are transparent.
        result = highlight_code_lines(pseudo, lines=[10, 11])
        self.play(result.fade)
        if result.indicate is not None:
            self.play(result.indicate)
        self.next_slide()

        mob, anim = code_explain(
            pseudo,
            lines=[10, 11],
            explanation="Edge relaxation",
        )
        self.add(mob)
        self.play(anim)
        self.next_slide()

        # ``bold_math=True`` wraps each match in ``\boldsymbol{...}`` and
        # ``math_color`` recolours the rendered math. Useful when the
        # algorithm's variables are the visual focus of the slide.
        styled = code_with_math(
            "norm($x$) = $\\sqrt{\\sum_{i=1}^{n} x_i^2}$",
            language="python",
            bold_math=True,
            math_color=GOLD,
        )
        styled.scale_to_fit_width(self.region.width * 0.7)
        styled.next_to(pseudo, DOWN, buff=0.4)
        self.play(Write(styled))
        self.next_slide()


class GraphAndArray(BaseSlide):
    def setup(self) -> None:
        super().setup()
        chrome = make_chrome(
            get_active_theme(),
            self.region,
            header="Components -- Node, Edge, ArrayMob, ArrayPointer",
        )
        self.add_to_canvas(**chrome.mobjects)
        self.region = chrome.body_region

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
        self.next_slide(name="GraphAndArray")

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
        self.region.place(arr, DOWN, buff=0.6)
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


class RegionAnchors(BaseSlide):
    def setup(self) -> None:
        super().setup()
        chrome = make_chrome(
            get_active_theme(),
            self.region,
            header=r"engine/region.py -- direction anchors + shrink + split + linspace",
        )
        self.add_to_canvas(**chrome.mobjects)
        self.region = chrome.body_region

    def construct(self) -> None:
        # Anchors are Manim direction vectors -- no strings. UL/UR/DL/DR
        # use the named diagonals; the literal corner names live on the
        # mobjects so viewers can read them off.
        markers = []
        for direction, label in (
            (UL, "UL"),
            (UR, "UR"),
            (DL, "DL"),
            (DR, "DR"),
            (ORIGIN, "ORIGIN"),
        ):
            mob = Caption(label)
            self.region.place(mob, direction, buff=0.25)
            markers.append(mob)
        self.play(*(Write(m) for m in markers))
        self.next_slide(name="RegionAnchors")

        self.region.shrink(left=2.5, right=2.5)
        sidebar = Caption("shrink(left=2.5, right=2.5) reflows subsequent placements")
        self.region.place(sidebar, ORIGIN)
        self.play(Write(sidebar))
        self.next_slide()

        self.region.reset()
        full = Caption("region.reset() restores the full frame")
        self.region.place(full, ORIGIN)
        self.play(Write(full))
        self.next_slide()

        # Region.split divides the region into k equal sub-regions along
        # an axis. Here we split horizontally into thirds and drop a
        # marker into the middle of each piece.
        self.play(*(Unwrite(m) for m in (*markers, full)))
        triptych = self.region.split(RIGHT, 3)
        labels = []
        for idx, sub in enumerate(triptych, start=1):
            cap = Caption(rf"split(RIGHT, 3)\\[2pt] piece {idx}")
            sub.place(cap, ORIGIN)
            labels.append(cap)
        self.play(*(Write(label) for label in labels))
        self.next_slide()

        self.play(*(Unwrite(label) for label in labels))
        points = self.region.linspace(RIGHT, 3)
        dots = VGroup(*(Dot(p, radius=0.08, color=GOLD) for p in points))
        caption = Caption("linspace(RIGHT, 3) keeps equal margins")
        self.region.place(caption, DOWN, buff=0.35)
        self.play(FadeIn(dots), Write(caption))
        self.next_slide()


class OutlineHelpers(OutlineScene):
    """``slides/outline.py`` -- typed outline parts and linspace progress dots."""

    def __init__(self, **kwargs):
        parts = [
            OutlinePart(
                title=Tex(r"Typed parts"),
                label=Caption(r"Typed\\parts"),
                visual=VGroup(Circle(radius=0.65), MathTex(r"P_1")).set_color(GOLD),
            ),
            OutlinePart(
                title=Tex(r"Progress from Region.linspace"),
                label=Caption(r"Region\\linspace"),
                visual=VGroup(Square(side_length=1.2), MathTex(r"x_i")).set_color(BLUE),
            ),
            OutlinePart(
                title=Tex(r"Mobject-native animation"),
                label=Caption(r"animate\\set\_index"),
                visual=VGroup(Triangle(), MathTex(r"\alpha")).set_color(GREEN),
            ),
        ]
        super().__init__(parts=parts, section_name="OutlineHelpers", **kwargs)

    def setup(self) -> None:
        super().setup()
        chrome = make_chrome(
            get_active_theme(),
            self.region,
            header=r"slides/outline.py -- OutlineScene + mobjects/outline.py",
        )
        self.add_to_canvas(**chrome.mobjects)
        self.region = chrome.body_region


class ExitAnimations(BaseSlide):
    def setup(self) -> None:
        super().setup()
        chrome = make_chrome(
            get_active_theme(),
            self.region,
            header=r"Remove + set\_exit\_animation + register\_exit + clear\_scene",
        )
        self.add_to_canvas(**chrome.mobjects)
        self.region = chrome.body_region

    def construct(self) -> None:
        keep = Tex(r"survives via clear\_scene(exclude=[this])")
        fade = Tex(r"default exit: Unwrite (Tex default)")
        shrink = Tex(r"per-instance: set\_exit\_animation(mob, ShrinkToCenter)")
        registered = Circle(radius=0.6, color=RED)

        # Per-type override: every Circle in this scene exits via FadeIn-reversed
        # (we cheat with ShrinkToCenter to keep things simple).
        register_exit(Circle, ShrinkToCenter)

        set_exit_animation(shrink, ShrinkToCenter)

        keep.shift(UP * 2.4)
        shrink.shift(DOWN * 1.8)
        registered.next_to(shrink, DOWN, buff=0.6)
        self.add(keep, fade, shrink, registered)
        self.next_slide(name="ExitAnimations")

        # clear_scene dispatches through exit_for, which checks per-instance
        # overrides first, then walks the type MRO, then falls back to FadeOut.
        self.clear_scene(exclude=[keep])
        self.next_slide()


class GeometryHelpers(BaseSlide):
    def setup(self) -> None:
        super().setup()
        chrome = make_chrome(
            get_active_theme(),
            self.region,
            header=r"engine/geometry.py -- convex hull + surrounding rect",
        )
        self.add_to_canvas(**chrome.mobjects)
        self.region = chrome.body_region

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
        self.next_slide(name="GeometryHelpers")

        a = Dot(LEFT * 3 + DOWN)
        b = Dot(RIGHT * 3 + UP)
        rect = get_surrounding_rectangle(a, b, buff=0.3)
        self.play(FadeIn(a, b), Write(rect))
        self.next_slide()


class GlyphMapTransform(BaseSlide):
    def setup(self) -> None:
        super().setup()
        chrome = make_chrome(
            get_active_theme(),
            self.region,
            header=r"engine/glyph\_map.py -- TransformByGlyphMap",
        )
        self.add_to_canvas(**chrome.mobjects)
        self.region = chrome.body_region

    def construct(self) -> None:
        eq1 = MathTex("f(x) = 4x^2 + 5x + 6").scale(1.4)
        eq2 = MathTex("f(-3) = 4(-3)^2 + 5(-3) + 6").scale(1.4)
        self.region.place(eq1, ORIGIN)
        eq2.move_to(eq1)
        self.add(eq1)
        self.next_slide(name="GlyphMapTransform")

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


class TrackingHelpers(BaseSlide):
    def setup(self) -> None:
        super().setup()
        chrome = make_chrome(
            get_active_theme(),
            self.region,
            header=r"engine/dynamics.py -- VT, DN + engine/geometry.py Vcis",
        )
        self.add_to_canvas(**chrome.mobjects)
        self.region = chrome.body_region

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
        self.region.place(face, ORIGIN)
        self.add(face, ticks, hand, readout)
        self.next_slide(name="TrackingHelpers")

        # `~vt` reads it; `vt @ x` returns an animate.set_value builder for play().
        self.play(angle @ (PI / 2), run_time=1.5)
        self.next_slide()
        self.play(angle @ (5 * PI / 6), run_time=1.5)
        self.next_slide()
        self.play(angle @ (-PI / 4), run_time=1.5)
        self.next_slide()


class ShapeAndDebug(BaseSlide):
    def setup(self) -> None:
        super().setup()
        chrome = make_chrome(
            get_active_theme(),
            self.region,
            header=r"engine/geometry.py SurroundingRectangleUnion + engine/debug.py",
        )
        self.add_to_canvas(**chrome.mobjects)
        self.region = chrome.body_region

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
        self.region.place(grid, ORIGIN)
        unions.move_to(grid)
        self.play(FadeIn(grid))
        self.play(*(Write(u) for u in unions))
        self.next_slide(name="ShapeAndDebug")

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


class ScalingHelpers(BaseSlide):
    """``engine/scaling.py`` -- multi-axis fit + stroke-aware scaling."""

    def setup(self) -> None:
        super().setup()
        chrome = make_chrome(
            get_active_theme(),
            self.region,
            header=r"engine/scaling.py -- scale\_to\_fit + scale\_with\_stroke\_width",
        )
        self.add_to_canvas(**chrome.mobjects)
        self.region = chrome.body_region

    def construct(self) -> None:
        # Split the body into two columns: original on the left, fit on the right.
        left, right = self.region.split(RIGHT, 2)

        eq = MathTex(r"\int_{-\infty}^{\infty} e^{-x^{2}}\,dx = \sqrt{\pi}")
        left.place(eq, ORIGIN)
        original_caption = Caption("original").next_to(eq, DOWN, buff=0.4)
        self.add(eq, original_caption)
        self.next_slide(name="ScalingHelpers")

        # ``scale_to_fit`` keeps aspect, picks the smallest required factor
        # to fit inside *all* supplied lengths, and subtracts a buff.
        fit = eq.copy()
        scale_to_fit(fit, len_x=right.width, len_y=right.height, buff=0.4)
        right.place(fit, ORIGIN)
        fit_caption = Caption("scale\\_to\\_fit(len\\_x, len\\_y, buff)").next_to(
            fit, DOWN, buff=0.4
        )
        self.play(FadeIn(fit), Write(fit_caption))
        self.next_slide()
