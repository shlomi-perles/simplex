"""Showcase deck -- exercises every Simplex-specific helper end-to-end.

Each scene targets one module so a reader can correlate the output with the
source. Most scenes still use the thin ``self.next_slide()`` cue alias so the
showcase can demonstrate older helpers, but new scenes should prefer explicit
``self.slide(...)`` and ``self.fragment(...)`` markers.

Slide numbering and the wall clock live in the web player shell. The showcase
renders only content chrome: a top helper title plus the Simplex logo footer.
Toggle the clock or counter from ``[web]`` in ``deck.toml``.
"""

import math
from collections.abc import Callable
from typing import Any, cast

import numpy as np
from manim import (
    LARGE_BUFF,
    MED_SMALL_BUFF,
    SMALL_BUFF,
    YELLOW,
    Animation,
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
    Mobject,
    Rectangle,
    ShrinkToCenter,
    Square,
    SurroundingRectangle,
    Tex,
    TransformMatchingShapes,
    Triangle,
    Unwrite,
    VGroup,
    VMobject,
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
    pseudocode_block,
    transform_code_lines,
)
from simplex.engine.debug import bounding_box, indexx_labels
from simplex.engine.dynamics import DN, VT
from simplex.engine.geometry import SurroundingRectangleUnion, get_surrounding_rectangle
from simplex.engine.ghost_fade import GhostSlideFade
from simplex.engine.glyph_map import TransformByGlyphMap
from simplex.engine.region import Region
from simplex.engine.scaling import scale_to_fit, scale_to_fit_mobject
from simplex.engine.text import Caption, TexPage, color_substrings
from simplex.mobjects import Array, ArrayPointer, Edge, Node
from simplex.slides import OutlinePart, OutlineScene, Slide

try:
    from slides.showcase_style import setup_showcase_chrome
except ModuleNotFoundError:  # direct ``manim slides/scenes.py ...`` execution
    from showcase_style import setup_showcase_chrome


type GlyphMapSpec = tuple[Any, ...]
type GlyphSpec = tuple[VMobject, VMobject, tuple[GlyphMapSpec, ...], dict[str, Any]]
type GlyphGridEntry = tuple[Region, VMobject, VMobject, tuple[GlyphMapSpec, ...], dict[str, Any]]


class TextHelpers(Slide):
    def setup(self) -> None:
        super().setup()
        setup_showcase_chrome(self, "engine/text.py -- Tex, Caption, TexPage, color_substrings")

    def construct(self) -> None:
        self.next_slide(name="Custom Slide's name")
        region_a, region_b, region_c = self.region.split_regions(DOWN, 3)
        body = Tex(r"Body paragraphs default to \textit{theme.typography.body}: $E = mc^2$.")
        self.region.place(body, UP)
        cap = Caption("Captions use the smaller theme.typography.caption font size.")
        cap.next_to(body, DOWN)
        pars_group = VGroup(body, cap)
        region_a.place(pars_group)

        self.play(Write(self.canvas["showcase_title"]), Write(pars_group))
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
        )
        region_b.place(page)
        self.play(Write(page))
        self.play(page.equation(0).animate.set_color(GOLD))
        self.next_slide()

        narrow = TexPage(
            r"\textbf{Same helper, narrower page.} Here \texttt{page\_width} is a "
            r"number of Manim units instead of a Region.",
            page_width=self.region.width * 0.62,
        )
        formula = MathTex(r"a^2 + b^2 = c^2")
        color_substrings(formula, {"a": RED, "b": BLUE, "c": YELLOW})
        region_c.place(narrow, UP)
        self.play(Write(narrow))
        self.next_slide()

        self.play(Write(formula))
        self.next_slide()

        self.clear_scene()


class CodeHelpers(Slide):
    def setup(self) -> None:
        super().setup()
        setup_showcase_chrome(
            self,
            "engine/code.py -- code_block + highlight + explain + transform + code_with_math",
        )

    def construct(self) -> None:
        snippet_bfs = (
            "def BFS(G,s):\n"
            "    queue ← Build Queue({s})\n"
            "    for each vertex u in V do:\n"
            "        dist[u] ← ∞\n"
            "    dist[s] ← 0\n"
            "    π[s] ← None\n\n"
            "    while queue ≠ ø do:\n"
            "        u = queue.pop(0)\n"
            "        for neighbor v of u & dist[v] = ∞:\n"
            "                queue.push(v)\n"
            "                dist[v] = dist[u] + 1\n"
            "                π[v] = u\n"
        )
        snippet_dfs = (
            "def DFS(G,s):\n"
            "    queue ← Build Queue({s})\n"
            "    Init dists to ∞, dist[s] ← 0\n"
            "    π[s] ← None\n\n"
            "    while queue ≠ ø do:\n"
            "        u = queue.pop()\n"
            "        for neighbor v of u & dist[v] = ∞:\n"
            "                queue.push(v)\n"
            "                dist[v] = dist[u] + 1\n"
            "                π[v] ← u\n                \n"
        )
        snippet_dfs_tex = (
            "def DFS($G$,$s$):\n"
            "    queue $\\leftarrow$ Build Queue({$s$})\n"
            "    Init dists to $\\infty$, dist[$s$] $\\leftarrow$ 0\n"
            "    $\\pi$[$s$] $\\leftarrow$ None\n\n"
            "    while queue $\\neq \\emptyset$ do:\n"
            "        $u$ = queue.pop()\n"
            "        for neighbor $v$ of $u$ & dist[$v$] = $\\infty$:\n"
            "                queue.push($v$)\n"
            "                dist[$v$] = dist[$u$] + 1\n"
            "                $\\pi$[$v$] $\\leftarrow$ $u$                \n"
        )
        bfs_code = code_block(snippet_bfs)
        dfs_code = code_block(snippet_dfs)
        dfs_code_tex = code_with_math(snippet_dfs_tex)
        self.region.scale_and_place(bfs_code)
        # scale_factor = dfs_code.line_numbers.lines_text.get_font_size() / bfs_code.line_numbers.lines_text.get_font_size()
        scale_factor = bfs_code.code_lines[0].height / dfs_code.code_lines[0].height
        dfs_code.scale(scale_factor)
        dfs_code_tex.scale(scale_factor)
        dfs_code.align_to(bfs_code, UL)
        dfs_code_tex.code_lines.align_to(dfs_code.code_lines, UL)
        self.play(Write(self.canvas["showcase_title"]), Write(bfs_code))
        self.next_slide()

        result = highlight_code_lines(bfs_code, lines=[1, 2, 3, 4, 5, 6])
        self.play(result.fade)
        if result.indicate is not None:
            self.play(result.indicate)
        self.next_slide()

        brace, anim = code_explain(
            bfs_code,
            lines=[9, 10],
            explanation="Dequeue\n+ expand neighbours",
        )
        self.play(anim)
        self.next_slide()
        self.play(Unwrite(brace))
        self.play(highlight_code_lines(bfs_code).fade)  # Fade-in all lines to prepare for transform
        self.play(transform_code_lines(bfs_code, dfs_code, {1: 1, 2: 2, 3: 3, 4: 3, 5: 3, 6: 4}))
        self.play(
            transform_code_lines(bfs_code, dfs_code, {8: 6, 9: 7, 10: 8, 11: 9, 12: 10, 13: 11})
        )
        self.next_slide()

        self.play(
            transform_code_lines(
                dfs_code, dfs_code_tex, {i: i for i in range(1, len(dfs_code_tex.code_lines) + 1)}
            )
        )
        self.next_slide()

        self.clear_scene()


class PseudocodeBlock(Slide):
    def setup(self) -> None:
        super().setup()
        setup_showcase_chrome(
            self,
            "engine/code.py -- pseudocode_block (algorithm2e + Code API)",
        )

    def construct(self) -> None:
        # ``pseudocode_block`` compiles algorithm2e LaTeX, then exposes
        # the rendered numbered rows as ``Code.code_lines``. That means
        # highlight/explain helpers target the visible algorithm numbers.
        algorithm = pseudocode_block(
            r"""
\SetArgSty{}
\SetKwInput{Input}{Input}
\SetKwInput{Output}{Output}
\Input{Adjacency matrix $A$ for $G=(V,E)$}
\Output{$M=VV^\top\in\mathbb{F}_2^{n\times n}$}
Build $\overline{G}=(V,\overline{E})$\;
Compute degeneracy ordering $v_1,\dots,v_n$ of $\overline{G}$\;
Set $r\leftarrow\delta^*(\overline{G})+3$ and initialize $V$\;
\For{$i\leftarrow n$ \KwTo $1$}{
  $S_i\leftarrow\{j>i:(v_i,v_j)\in\overline{E}\}$\;
  Choose $x_i\in\mathbb{F}_2^r$ solving $B_i x_i=b_i$\;
}
Return $M\leftarrow VV^\top$ over $\mathbb{F}_2$\;
""",
            caption=r"\textbf{Degeneracy-Guided Assignment}",
        )

        self.region.scale_and_place(algorithm)
        self.play(Write(self.canvas["showcase_title"]), Write(algorithm))

        result = highlight_code_lines(algorithm, lines=[4, 5, 6, 7])
        self.play(result.fade)
        if result.indicate is not None:
            self.play(result.indicate)
        self.next_slide()

        _mob, anim = code_explain(
            algorithm,
            lines=[4, 5, 6],
            explanation="Reverse-order\nassignment",
        )
        self.play(anim)
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
        split_regions[0].scale_and_place(graph)
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
        split_regions[1].scale_and_place(arr_cp_group)
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

        self.play(cast(Any, self.region.animate.shrink(left=2.5, right=2.5)), Write(sidebar))
        self.next_slide()

        full = Caption("region.reset() restores the full frame").move_to(sidebar)
        self.play(cast(Any, self.region.animate.reset()), TransformMatchingShapes(sidebar, full))
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
        self.region.place(caption, DOWN)
        self.play(FadeIn(dots), Write(caption))
        self.next_slide()
        self.clear_scene()


class OutlineHelpers(OutlineScene):
    """``slides/outline.py`` -- typed outline parts and linspace progress dots."""

    def __init__(self, **kwargs: Any) -> None:
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
        intro: list[Any] = [Write(self.canvas["showcase_title"]), self.progress_bar.appear()]
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
        rect = get_surrounding_rectangle(a, b)
        self.region.place(VGroup(a, b, rect), ORIGIN)
        self.play(Write(self.canvas["showcase_title"]), FadeIn(a, b), Write(rect))
        self.next_slide()
        self.clear_scene()


class GlyphMapTransform(Slide):
    def setup(self) -> None:
        super().setup()
        setup_showcase_chrome(self, "engine/glyph_map.py -- TransformByGlyphMap")

    def construct(self) -> None:
        spec_factories: tuple[Callable[[], GlyphSpec], ...] = (
            self._glyph_specs_1,
            self._glyph_specs_2,
            self._glyph_specs_3,
            self._glyph_specs_4,
            self._glyph_specs_5,
            self._glyph_specs_6,
            self._glyph_specs_7,
            self._glyph_specs_8,
        )
        specs = tuple(factory() for factory in spec_factories)
        cells = self._grid_regions(row_counts=(3, 3, 2), cols=3)
        entries: list[GlyphGridEntry] = []
        starts = VGroup()
        labels = VGroup()
        animations: list[Animation] = []

        for idx, (cell, (src, dst, glyph_map, kwargs)) in enumerate(
            zip(cells, specs, strict=True),
            start=1,
        ):
            pair = VGroup(src, dst)
            cell.scale_and_place(pair, buff=MED_SMALL_BUFF)
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

    def _grid_regions(self, *, row_counts: tuple[int, ...], cols: int) -> list[Region]:
        rows = self.region.split_regions(DOWN, len(row_counts))
        cells: list[Region] = []
        for row, count in zip(rows, row_counts, strict=True):
            cells.extend(row.split_regions(RIGHT, cols)[:count])
        return cells

    @staticmethod
    def _realign_if_overlaid(src: Mobject, dst: Mobject) -> None:
        if np.allclose(src.get_center(), dst.get_center()):
            dst.move_to(src)

    @staticmethod
    def _apply_min_font_size(entries: list[GlyphGridEntry]) -> None:
        font_mobjects: list[Any] = [
            mob for _, src, dst, _, _ in entries for mob in (src, dst) if hasattr(mob, "font_size")
        ]
        if not font_mobjects:
            return
        font_size = min(float(mob.font_size) for mob in font_mobjects)
        for mob in font_mobjects:
            mob.font_size = font_size

    def _glyph_specs_1(self) -> GlyphSpec:
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

    def _glyph_specs_2(self) -> GlyphSpec:
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

    def _glyph_specs_3(self) -> GlyphSpec:
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

    def _glyph_specs_4(self) -> GlyphSpec:
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

    def _glyph_specs_5(self) -> GlyphSpec:
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

    def _glyph_specs_6(self) -> GlyphSpec:
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

    def _glyph_specs_7(self) -> GlyphSpec:
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

    def _glyph_specs_8(self) -> GlyphSpec:
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
        if not isinstance(hand, VMobject):
            raise TypeError("Tracking hand must be a vectorized mobject for Write().")
        readout = DN(
            lambda: math.degrees(~angle) % 360,
            num_decimal_places=0,
            unit=r"^{\circ}",
        )
        readout.scale(0.9)
        readout.next_to(face, DOWN, buff=0.5)
        # `~vt` reads it; `vt @ x` returns an animate.set_value builder for play().

        self.play(
            Write(self.canvas["showcase_title"]),
            Write(hand),
            Write(readout),
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
        dots = tuple(Dot(radius=0.15, color=GOLD) for _ in range(rows * cols))
        grid = VGroup(*dots)
        grid.arrange_in_grid(rows=rows, cols=cols, buff=0.8)
        region_a, region_b, region_c = self.region.split_regions(RIGHT, 3)
        region_b.scale_and_place(grid)
        rendered_dot_radius = min(dots[0].width, dots[0].height) / 2

        groups = (
            ([0, 1, 6, 7], RED),
            ([3, 4, 5, 9, 10, 11], GREEN),
            ([12, 13, 18, 19, 20, 21], BLUE),
        )
        unions = VGroup(
            *(
                SurroundingRectangleUnion(
                    *(grid[i] for i in indices),
                    buff=rendered_dot_radius * 1.2,
                    unbuff=rendered_dot_radius * 0.3,
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
        region_a.scale_and_place(eq)
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
        left.scale_and_place(eq, buff=LARGE_BUFF)
        original_caption = Caption(r"Region.scale\_and\_place(...)")
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
        scale_to_fit_mobject(boxed, eq)
        rect_surround = SurroundingRectangle(boxed, buff=0)
        VGroup(boxed, rect_surround).move_to(eq.get_center())
        self.play(Write(boxed), Create(rect_surround))
        self.next_slide()
        self.clear_scene()
