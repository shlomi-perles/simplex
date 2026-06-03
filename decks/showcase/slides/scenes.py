"""Showcase deck -- exercises every Simplex-specific helper end-to-end.

Each scene targets one module so a reader can correlate the output with the
source. The first ``self.next_slide()`` call in each scene is bare and
auto-promotes to a main slide named after the class
(``DFSLecture -> "DFS Lecture"``); subsequent bare calls are sub-stops.

Slide numbering and the wall clock live in the RevealJS host. The showcase
renders only content chrome: a top helper title plus the Simplex logo footer.
Toggle the clock or counter from ``[web]`` in ``deck.toml``.
"""

import math

import numpy as np
from manim import (
    LARGE_BUFF,
    MED_SMALL_BUFF,
    SMALL_BUFF,
    AnimationGroup,
    BLUE,
    DL,
    DOWN,
    DR,
    GOLD,
    GREEN,
    LEFT,
    MED_LARGE_BUFF,
    ORIGIN,
    PI,
    RED,
    RIGHT,
    UL,
    UP,
    UR,
    Arrow,
    Circle,
    Create,
    Dot,
    FadeIn,
    FadeOut,
    GrowFromCenter,
    Line,
    MathTex,
    Rectangle,
    ShrinkToCenter,
    Square,
    SurroundingRectangle,
    Tex,
    TransformMatchingShapes,
    Triangle,
    Unwrite,
    VGroup,
    Write,
    always_redraw,
)
from manim.utils.space_ops import rotate_vector

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
from simplex.engine.geometry import SurroundingRectangleUnion, get_surrounding_rectangle
from simplex.engine.ghost_fade import GhostSlideFade
from simplex.engine.glyph_map import TransformByGlyphMap
from simplex.engine.scaling import scale_to_fit, scale_to_fit_mobject
from simplex.engine.text import Caption, TexPage, color_tex
from simplex.mobjects import Array, ArrayPointer, Edge, Node
from simplex.slides import OutlinePart, OutlineScene, Slide

try:
    from slides.showcase_style import setup_showcase_chrome
except ModuleNotFoundError:  # direct ``manim slides/scenes.py ...`` execution
    from showcase_style import setup_showcase_chrome


class TextHelpers(Slide):
    def setup(self) -> None:
        super().setup()
        setup_showcase_chrome(self, "engine/text.py -- Tex, Caption, TexPage, color_tex")

    def construct(self) -> None:
        body = Tex(r"Body paragraphs default to \textit{theme.typography.body}: $E = mc^2$.")
        self.region.place(body, UP)
        self.play(Write(self.canvas["showcase_title"]), Write(body))
        self.next_slide(name="Custom Slide's name")

        cap = Caption("Captions use the smaller theme.typography.caption font size.")
        cap.next_to(body, DOWN)
        self.play(Write(cap))
        self.next_slide()

        page = TexPage(
            r"\textbf{TexPage.} Pass a \texttt{Region} as \texttt{page\_width}; "
            r"Simplex measures how many Manim units one LaTeX centimeter occupies "
            r"at the active font size, subtracts \texttt{2 * buff}, and chooses the "
            r"matching minipage width."
            r"\["
            r"\begin{aligned}"
            r"\texttt{usable} &= \texttt{page\_width} - 2\texttt{buff}\\"
            r"\texttt{cm} &= \texttt{usable}/\texttt{munits\_per\_cm(font\_size)}"
            r"\end{aligned}"
            r"\]"
            r"Display equations are isolated, so \texttt{page.equation(0)} can be "
            r"animated directly.",
            page_width=self.region,
            math_spacing=2,
        )
        page.next_to(cap, DOWN)
        self.play(Write(page))
        self.play(page.equation(0).animate.set_color(GOLD))
        self.next_slide()

        narrow = TexPage(
            r"\textbf{Same helper, narrower page.} Here \texttt{page\_width} is a "
            r"number of Manim units instead of a Region.",
            page_width=self.region.width * 0.62,
        )
        narrow.next_to(page, DOWN)
        self.play(Write(narrow))
        self.next_slide()

        formula = MathTex(r"a^2 + b^2 = c^2")
        color_tex(formula, {"a": "#FF6B6B", "b": "#4ECDC4", "c": "#FFD93D"}, tex_class=MathTex)
        formula.next_to(narrow, DOWN)
        self.play(Write(formula))
        self.clear_scene()


class CodeHelpers(Slide):
    def setup(self) -> None:
        super().setup()
        setup_showcase_chrome(
            self,
            "engine/code.py -- code_block + highlight + explain + transform",
        )

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
        code = code_block(snippet)
        scale_to_fit(code, len_x=self.region.width * 0.55, len_y=self.region.height * 0.55)
        self.region.place(code)
        self.play(Write(self.canvas["showcase_title"]), FadeIn(code))

        result = highlight_code_lines(code, lines=[5, 6, 7, 8, 9])
        self.play(result.fade)
        if result.indicate is not None:
            self.play(result.indicate)
        self.next_slide()

        mob, anim = code_explain(
            code,
            lines=[5, 6],
            explanation="Dequeue\n+\nexpand neighbours",
        )
        self.add(mob)
        self.play(anim)
        self.next_slide()

        # transform_code_lines morphs one Code block into another by line
        # mapping. Here we show a refactored two-liner side-by-side.
        refactor_src = code_block("for nb in graph[node]:\n    if nb not in visited:\n")
        refactor_dst = code_block("for nb in graph[node] - visited:\n    visited.add(nb)\n")
        refactor_src.scale(0.6)
        refactor_src.next_to(code, DOWN, buff=0.4)
        refactor_dst.scale(0.6)
        refactor_dst.move_to(refactor_src)
        self.play(FadeIn(refactor_src))
        self.play(transform_code_lines(refactor_src, refactor_dst, {1: 1, 2: 2}))
        self.next_slide()
        self.clear_scene()


class CodeWithMath(Slide):
    def setup(self) -> None:
        super().setup()
        setup_showcase_chrome(
            self,
            "engine/code.py -- code_with_math (inline LaTeX in code)",
        )

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
        )
        scale_to_fit(pseudo, len_x=self.region.width * 0.7, len_y=self.region.height * 0.7)
        self.region.place(pseudo)
        self.play(Write(self.canvas["showcase_title"]), FadeIn(pseudo))

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
            explanation="Edge\n+\nrelaxation",
        )
        self.add(mob)
        self.play(anim)
        self.next_slide()

        # ``bold_math=True`` wraps each match in ``\boldsymbol{...}`` and
        # ``math_color`` recolours the rendered math. Useful when the
        # algorithm's variables are the visual focus of the slide.
        styled = code_with_math(
            "norm($x$) = $\\sqrt{\\sum_{i=1}^{n} x_i^2}$",
            bold_math=True,
            math_color=GOLD,
        )
        scale_to_fit(styled, len_x=self.region.width * 0.5, len_y=self.region.height * 0.2)
        styled.next_to(pseudo, DOWN, buff=0.4)
        self.play(Write(styled))
        self.next_slide()
        self.clear_scene()


class GraphAndArray(Slide):
    def setup(self) -> None:
        super().setup()
        setup_showcase_chrome(self, "Components -- Node, Edge, Array, ArrayPointer")

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
        # Edges before nodes so the nodes render on top of the connecting lines.
        graph = VGroup(*edges, n1, n2, n3)
        split_regions = self.region.split_regions(DOWN, 2)
        split_regions[0].scale_and_place(graph, ORIGIN, buff=MED_LARGE_BUFF)
        arr = Array(
            ["-", "8", "1", "3", "9"],
            label="A:",
            show_indices=True,
            start_index=1,
        )
        arr_cp = arr.copy()
        arr_cp.animate_append("5").begin()
        cp_pointer = ArrayPointer(arr_cp, 2, label="here")
        arr_cp_group = VGroup(arr_cp, cp_pointer)
        split_regions[1].scale_and_place(arr_cp_group, ORIGIN, buff=0.5)
        scale_to_fit_mobject(arr, arr_cp)
        arr.move_to(arr_cp).align_to(arr_cp, LEFT)
        self.play(Write(self.canvas["showcase_title"]), Write(arr), Write(graph))
        self.next_slide()

        self.play(arr.animate_set_value(1, "b"))
        self.play(arr.indicate(2))
        self.play(arr.animate_append("5"))
        self.play(arr.animate_swap(2, 4))
        self.next_slide()

        pointer = ArrayPointer(arr, 2, label="here")
        self.play(Write(pointer))
        self.play(pointer.animate_to(4))
        self.next_slide()
        self.clear_scene()


class RegionAnchors(Slide):
    def setup(self) -> None:
        super().setup()
        setup_showcase_chrome(
            self,
            r"engine/region.py -- direction anchors + shrink + split + linspace",
        )

    def construct(self) -> None:
        # Anchors are Manim direction vectors -- no strings. UL/UR/DL/DR
        # use the named diagonals; the literal corner names live on the
        # mobjects so viewers can read them off.

        sidebar = Caption("region.shrink(left=2.5, right=2.5) reflows subsequent placements")
        self.region.place(sidebar, UP)
        self.region.update(top=sidebar)
        markers = []
        all_directions = (
            (UL, "UL"),
            (UR, "UR"),
            (DL, "DL"),
            (DR, "DR"),
            (ORIGIN, "ORIGIN"),
        )
        for direction, label in all_directions:
            mob = Caption(label)
            self.region.always_place(mob, direction, buff=SMALL_BUFF)
            markers.append(mob)
        self.play(Write(self.canvas["showcase_title"]), *(Write(m) for m in markers))
        self.next_slide()

        self.play(self.region.animate.shrink(left=2.5, right=2.5), Write(sidebar))
        self.next_slide()

        full = Caption("region.reset() restores the full frame").move_to(sidebar)
        self.play(self.region.animate.reset(), TransformMatchingShapes(sidebar, full))
        self.next_slide()

        # Region.split_regions divides the region into k equal sub-regions along
        # an axis. Here we split horizontally into thirds and drop a
        # marker into the middle of each piece.
        self.play(*(Unwrite(m) for m in (*markers, full)))
        triptych = self.region.split_regions(RIGHT, 3)
        labels = []
        for idx, sub in enumerate(triptych, start=1):
            cap = Caption(rf"split\_regions(RIGHT, 3)\\[2pt] piece {idx}")
            sub.place(cap, ORIGIN)
            labels.append(cap)
        self.play(*(Write(label) for label in labels))
        self.next_slide()

        self.play(*(Unwrite(label) for label in labels))
        points = self.region.linspace(RIGHT, 3)
        dots = VGroup(*(Dot(p, color=GOLD) for p in points))
        caption = Caption("linspace(RIGHT, 3) keeps equal margins")
        self.region.place(caption, DOWN, buff=0.35)
        self.play(FadeIn(dots), Write(caption))
        self.next_slide()
        self.clear_scene()


class OutlineHelpers(OutlineScene):
    """``slides/outline.py`` -- typed outline parts and linspace progress dots."""

    def __init__(self, **kwargs):
        parts = [
            OutlinePart(
                title=Tex(r"Typed parts"),
                label=Caption(r"Typed\\parts"),
                visual=VGroup(Circle(), MathTex(r"P_1")).set_color(GOLD),
            ),
            OutlinePart(
                title=Tex(r"Progress from Region.linspace"),
                label=Caption(r"Region\\linspace"),
                visual=VGroup(Square(), MathTex(r"x_i")).set_color(BLUE),
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
        setup_showcase_chrome(self, r"slides/outline.py -- OutlineScene + mobjects/outline.py")

    def reveal_outline(self) -> None:
        self.outline_started = True
        intro = [Write(self.canvas["showcase_title"]), self.progress_bar.appear()]
        intro.extend(FadeIn(mob) for mob in self.initial_mobjects.submobjects[1:])
        self.play(AnimationGroup(*intro, lag_ratio=0.04))


class ExitAnimations(Slide):
    def setup(self) -> None:
        super().setup()
        setup_showcase_chrome(
            self,
            "Remove + set_exit_animation + register_exit + clear_scene",
        )

    def construct(self) -> None:
        keep = Tex(r"survives via clear\_scene(exclude=[this])")
        fade = Tex(r"default exit: Unwrite (Tex default)")
        shrink = Tex(r"per-instance: set\_exit\_animation(mob, ShrinkToCenter)")
        registered = Circle(radius=0.6, color=RED)
        region_a, region_b, region_c = self.region.split_regions(DOWN, 3)
        region_a.place(keep, ORIGIN)
        region_b.place(fade, ORIGIN)

        # Per-type override: every Circle in this scene exits via FadeIn-reversed
        # (we cheat with ShrinkToCenter to keep things simple).
        register_exit(Circle, ShrinkToCenter)

        set_exit_animation(shrink, ShrinkToCenter)

        registered.next_to(shrink, DOWN)
        region_c.place(VGroup(shrink, registered), ORIGIN)

        self.play(
            Write(self.canvas["showcase_title"]),
            Write(keep),
            Write(fade),
            Write(shrink),
            FadeIn(registered),
        )
        self.next_slide()

        # clear_scene dispatches through exit_for, which checks per-instance
        # overrides first, then walks the type MRO, then falls back to FadeOut.
        self.clear_scene(exclude=[keep])
        self.next_slide()
        self.clear_scene()


class GeometryHelpers(Slide):
    def setup(self) -> None:
        super().setup()
        setup_showcase_chrome(
            self,
            r"engine/geometry.py -- rotated surrounding rect (use manim.ConvexHull directly for hulls)",
        )

    def construct(self) -> None:
        a = Dot(LEFT * 3 + DOWN)
        b = Dot(RIGHT * 3 + UP)
        rect = get_surrounding_rectangle(a, b, buff=0.3)
        self.region.place(VGroup(a, b, rect), ORIGIN)
        self.play(Write(self.canvas["showcase_title"]), FadeIn(a, b), Write(rect))
        self.next_slide()
        self.clear_scene()


class GlyphMapTransform(Slide):
    def setup(self) -> None:
        super().setup()
        setup_showcase_chrome(self, "engine/glyph_map.py -- TransformByGlyphMap")

    def construct(self) -> None:
        specs = [getattr(self, f"_glyph_specs_{idx}")() for idx in range(1, 9)]
        cells = self._grid_regions(row_counts=(3, 3, 2), cols=3)
        entries = []
        starts = VGroup()
        labels = VGroup()
        animations = []

        for idx, (cell, (src, dst, glyph_map, kwargs)) in enumerate(
            zip(cells, specs, strict=True),
            start=1,
        ):
            pair = VGroup(src, dst)
            cell.scale_and_place(pair, ORIGIN, buff=MED_SMALL_BUFF)
            self._realign_if_overlaid(src, dst)
            label = Caption(str(idx))
            cell.place(label, UL, buff=SMALL_BUFF)
            entries.append((cell, src, dst, glyph_map, kwargs))
            starts.add(src)
            labels.add(label)

        self._apply_min_font_size(entries)
        for cell, src, dst, glyph_map, kwargs in entries:
            cell.place(VGroup(src, dst), ORIGIN)
            self._realign_if_overlaid(src, dst)
            animations.append(TransformByGlyphMap(src, dst, *glyph_map, **kwargs))

        self.play(
            Write(self.canvas["showcase_title"]),
            *(FadeIn(src) for src in starts),
            *(FadeIn(label) for label in labels),
        )
        self.play(*animations)
        self.next_slide()
        self.clear_scene()

    def _grid_regions(self, *, row_counts: tuple[int, ...], cols: int):
        rows = self.region.split_regions(DOWN, len(row_counts))
        cells = []
        for row, count in zip(rows, row_counts, strict=True):
            cells.extend(row.split_regions(RIGHT, cols)[:count])
        return cells

    @staticmethod
    def _realign_if_overlaid(src, dst) -> None:
        if np.allclose(src.get_center(), dst.get_center()):
            dst.move_to(src)

    @staticmethod
    def _apply_min_font_size(entries) -> None:
        font_mobjects = [
            mob for _, src, dst, _, _ in entries for mob in (src, dst) if hasattr(mob, "font_size")
        ]
        if not font_mobjects:
            return
        font_size = min(float(mob.font_size) for mob in font_mobjects)
        for mob in font_mobjects:
            mob.font_size = font_size

    def _glyph_specs_1(self):
        exp1 = MathTex("f(x) = 4x^2 + 5x + 6")
        exp2 = MathTex("f(-3) = 4(-3)^2 + 5(-3) + 6").move_to(exp1)
        return (
            exp1,
            exp2,
            (
                ([2], [2, 3]),
                ([6], [7, 8, 9, 10]),
                ([10], [14, 15, 16, 17]),
            ),
            {},
        )

    def _glyph_specs_2(self):
        exp1 = MathTex("ax^2 + bx + c = 0")
        exp2 = MathTex("x^2 + \\frac{b}{a}x + \\frac{c}{a} = 0").move_to(exp1)
        return (
            exp1,
            exp2,
            (
                ([0], [5], {"path_arc": 2 / 3 * PI}),
                ([0], [10], {"path_arc": 1 / 2 * PI}),
                ([], [4, 9]),
            ),
            {},
        )

    def _glyph_specs_3(self):
        exp1 = MathTex("\\frac{x^2y^3}{w^4z^{-8}}")
        exp2 = MathTex("\\frac{x^2y^3z^8}{w^4}").move_to(exp1)
        return (
            exp1,
            exp2,
            (
                ([7, 9], [4, 5]),
                ([8], [], {"shift": UP}),
            ),
            {},
        )

    def _glyph_specs_4(self):
        exp1 = MathTex("{ { 3x+2y \\over 2x+y } + 12z")
        exp2 = MathTex("\\left( { 2x+y \\over 3x+2y } \\right) ^ {-1} + 12z").move_to(exp1)
        return (
            exp1,
            exp2,
            (
                ([0, 1, 2, 3, 4], [6, 7, 8, 9, 10], {"path_arc": PI}),
                ([6, 7, 8, 9], [1, 2, 3, 4], {"path_arc": PI}),
                ([], [0], {"delay": 0.5}),
                ([], [11], {"delay": 0.5}),
                ([], [12, 13], {"delay": 0.5}),
            ),
            {"default_introducer": Write},
        )

    def _glyph_specs_5(self):
        exp1 = MathTex("1 \\over 3r+\\theta")
        exp2 = MathTex("\\left( 3r+\\theta \\right) ^ {-1}").move_to(exp1)
        return (
            exp1,
            exp2,
            (
                ([2, 3, 4, 5], [1, 2, 3, 4], {"path_arc": -2 / 3 * PI}),
                ([0, 1], FadeOut, {"run_time": 0.5}),
                (GrowFromCenter, [0, 5, 6, 7], {"delay": 0.25}),
            ),
            {"introduce_individually": True},
        )

    def _glyph_specs_6(self):
        exp1 = MathTex("4x^2 - x^2 + 5x + 3x - 7")
        exp2 = MathTex("3x^2 + 8x - 7")
        VGroup(exp1, exp2).arrange(DOWN, buff=0.35)
        return (
            exp1,
            exp2,
            (
                ([0, 3], [0]),
                ([1, 2], [1, 2]),
                ([4, 5], [1, 2]),
                ([7, 8, 9, 10, 11], [4, 5]),
            ),
            {"from_copy": True},
        )

    def _glyph_specs_7(self):
        exp1 = MathTex("1 \\over x")
        exp2 = MathTex("{ { 1 \\over x } - { 1 \\over x } } + 10").move_to(exp1)
        return (
            exp1,
            exp2,
            (
                ([0, 1, 2], [0, 1, 2]),
                ([0, 1, 2], [4, 5, 6]),
            ),
            {"default_introducer": Write, "auto_fade": True},
        )

    def _glyph_specs_8(self):
        exp1 = MathTex("\\sin(\\arctan(x))")
        exp2 = MathTex("{ {x} \\over {\\sqrt{1+x^2}} }").move_to(exp1)
        return (
            exp1,
            exp2,
            (
                ([11], [0]),
                ([11], [6]),
            ),
            {
                "auto_morph": True,
                "auto_resolve_kwargs": {"path_arc": PI / 3, "lag_ratio": 0.03, "delay": 0.25},
            },
        )


class TrackingHelpers(Slide):
    def setup(self) -> None:
        super().setup()
        setup_showcase_chrome(
            self,
            "engine/dynamics.py -- VT, DN (vectors come from vanilla manim rotate_vector)",
        )

    def construct(self) -> None:
        # A clock-style pointer driven by a VT angle. Use manim's vanilla
        # ``rotate_vector`` for unit-vector math -- no Simplex wrapper.
        angle = VT(0.0)
        face = Circle(radius=2.0, color=BLUE).set_stroke(width=2)
        ticks = VGroup(
            *(
                Line(
                    2.0 * rotate_vector(RIGHT, k * PI / 6),
                    1.85 * rotate_vector(RIGHT, k * PI / 6),
                    stroke_width=2,
                )
                for k in range(12)
            )
        )
        # Group the face and ticks so they move together; the body region's
        # center is not the frame center once the footer carves space off
        # the bottom.
        clock = VGroup(face, ticks)
        self.region.place(clock, ORIGIN)
        hand = always_redraw(
            lambda: Arrow(
                start=face.get_center(),
                end=face.get_center() + 1.7 * rotate_vector(RIGHT, ~angle),
                buff=0.0,
                color=GOLD,
            )
        )
        readout = DN(
            lambda: math.degrees(~angle) % 360,
            num_decimal_places=0,
            unit=r"^{\circ}",
        )
        readout.scale(0.9)
        readout.next_to(face, DOWN, buff=0.5)
        # `~vt` reads it; `vt @ x` returns an animate.set_value builder for play().

        self.play(
            *(Write(mob) for mob in (self.canvas["showcase_title"], hand, readout)),
            Create(ticks),
            GrowFromCenter(face),
        )
        self.play(angle @ (PI / 2), run_time=1.5)
        self.next_slide()
        self.play(angle @ (5 * PI / 6), run_time=1.5)
        self.next_slide()
        self.play(angle @ (-PI / 4), run_time=1.5)
        self.next_slide()
        self.clear_scene()


class ShapeAndDebug(Slide):
    def setup(self) -> None:
        super().setup()
        setup_showcase_chrome(
            self,
            r"engine/geometry.py SurroundingRectangleUnion + engine/debug.py",
        )

    def construct(self) -> None:
        # 6x4 grid of dots; group three subsets and surround each with a single
        # merged polygon (the rectangles for adjacent dots union together).
        rows, cols = 4, 6
        grid = VGroup(Dot(radius=0.15, color=GOLD) for _ in range(rows * cols))
        grid.arrange_in_grid(rows=rows, cols=cols, buff=0.8)
        region_a, region_b, region_c = self.region.split_regions(RIGHT, 3)
        region_b.scale_and_place(grid, ORIGIN, buff=MED_LARGE_BUFF)

        groups = (
            ([0, 1, 6, 7], RED),
            ([3, 4, 5, 9, 10, 11], GREEN),
            ([12, 13, 18, 19, 20, 21], BLUE),
        )
        unions = VGroup(
            *(
                SurroundingRectangleUnion(
                    *(grid[i] for i in indices),
                    buff=grid[0].radius * 1.2,
                    unbuff=grid[0].radius * 0.8,
                    corner_radius=0.12,
                    stroke_color=color,
                )
                for indices, color in groups
            )
        )
        self.play(Write(self.canvas["showcase_title"]), Create(grid))
        self.play(*(Write(u) for u in unions))
        self.next_slide()

        # Multi-color index labels for a multi-string MathTex.
        eq = MathTex(r"\sin\!\left(", r"{a^2 + b^2}", r"\over", r"{3n + 1}", r"\right)")
        region_a.scale_and_place(eq, ORIGIN, buff=MED_LARGE_BUFF)
        labels = indexx_labels(eq)
        self.play(Write(eq), FadeIn(labels))
        self.next_slide()

        # bounding_box(always=True) tracks an animated mob.
        bounding_rect = Rectangle()
        region_c.scale_and_place(bounding_rect, UP, buff=LARGE_BUFF)
        bounding_rect_targ = bounding_rect.copy().rotate(PI / 6)
        region_c.place(bounding_rect_targ, DOWN)
        bb = bounding_box(bounding_rect, always=True, include_center=True)
        self.play(Write(bounding_rect), FadeIn(bb))
        self.play(
            bounding_rect.animate.move_to(bounding_rect_targ.get_center()).rotate(PI / 6),
            run_time=1.5,
        )
        self.next_slide()

        # GhostSlideFade: drift+fade cue that cleans itself up.
        ghost = Circle()
        scale_to_fit_mobject(ghost, region_c, buff=LARGE_BUFF)
        self.region.place(ghost, UP)
        self.play(GhostSlideFade(ghost, shift_vector=DOWN, lifetime=1.5))
        self.next_slide()
        self.clear_scene()


class ScalingHelpers(Slide):
    """``engine/scaling.py`` -- multi-axis fit + stroke-aware scaling."""

    def setup(self) -> None:
        super().setup()
        setup_showcase_chrome(
            self,
            "engine/scaling.py -- scale_to_fit + scale_to_fit_mobject + Region.scale_and_place",
        )

    def construct(self) -> None:
        # Split the body into two columns: original on the left, fit on the right.
        left, right = self.region.split_regions(RIGHT, 2)

        eq = MathTex(r"\int_{-\infty}^{\infty} e^{-x^{2}}\,dx = \sqrt{\pi}")
        left.scale_and_place(eq, ORIGIN, buff=MED_LARGE_BUFF).scale(0.5)
        original_caption = Caption(r"Region.scale\_and\_place(...).scale(0.5)")
        original_caption.next_to(eq, DOWN, buff=0.4)
        self.play(Write(self.canvas["showcase_title"]), Write(eq), Write(original_caption))

        # ``scale_to_fit`` keeps aspect, picks the smallest required factor
        # to fit inside *all* supplied lengths, and subtracts a buff.
        fit = eq.copy()
        scale_to_fit(fit, len_x=right.width, len_y=right.height / 2, buff=MED_LARGE_BUFF)
        right.place(fit, ORIGIN)
        fit_caption = Caption("scale\\_to\\_fit(len\\_x, len\\_y, buff)")
        fit_caption.next_to(fit, DOWN, buff=MED_LARGE_BUFF)
        self.play(Write(fit), Write(fit_caption))
        self.next_slide()

        # ``scale_to_fit_mobject`` takes another mobject's bbox as the target,
        # so we can fit a copy of eq inside the bounding box of an existing
        # mobject (here, the original ``eq`` on the left).
        boxed = MathTex(r"\sum_{k=1}^{\infty} \frac{1}{k^{2}} = \frac{\pi^{2}}{6}")
        scale_to_fit_mobject(boxed, eq, buff=MED_SMALL_BUFF)
        rect_surround = SurroundingRectangle(boxed, buff=0)
        VGroup(boxed, rect_surround).move_to(eq.get_center())
        self.play(Write(boxed), Create(rect_surround))
        self.next_slide()
        self.clear_scene()
