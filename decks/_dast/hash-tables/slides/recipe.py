"""Hash Table Recipe -- build a hash table piece by piece, then chaining."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from manim import (
    DOWN,
    LEFT,
    RIGHT,
    UP,
    AnimationGroup,
    BraceLabel,
    DrawBorderThenFill,
    FadeIn,
    MathTex,
    SVGMobject,
    Tex,
    Text,
    Title,
    Transform,
    TransformMatchingTex,
    Unwrite,
    VGroup,
    WHITE,
    Write,
    config,
)

from simplex.engine.text import color_tex
from simplex.slides import BaseSlide

from utils import (
    FUNCS_COLOR,
    HASH_TABLE_FUNCS_TITLE_BUFF,
    SELECT_KEY_COLOR,
    SUB_TITLES_SCALE,
    compile_code_tex_line,
    get_func_text,
    get_hash_table_subtitles,
    get_main_hash_table_example,
)

ASSETS = Path(__file__).resolve().parent.parent / "assets" / "figures"


class HashTableRecipe(BaseSlide):
    def construct(self) -> None:
        np.random.seed(0)
        self.next_slide(name="Hash Table Recipe")
        title = Title("Hash Table Recipe")
        self.play(Write(title))

        frame_center, ht = get_main_hash_table_example(title)
        array_text, keys_text, hash_function_text = get_hash_table_subtitles(ht)

        # ---- array first -----------------------------------------------
        self.next_slide()
        array_coords = ht.array.get_center()
        ht.array.move_to(frame_center)
        array_text.scale(1 / SUB_TITLES_SCALE).match_x(ht.array)
        keys_text.scale(1 / SUB_TITLES_SCALE)
        self.play(Write(array_text))
        self.play(Write(ht.array))

        # ---- keys ------------------------------------------------------
        self.next_slide()
        self.play(
            array_text.animate.scale(SUB_TITLES_SCALE).set_x(array_coords[0]),
            ht.array.animate.move_to(array_coords),
        )
        keys_coords = ht.keys.get_center()
        ht.keys.move_to(frame_center)
        self.play(Write(keys_text))
        self.play(Write(ht.keys))

        # ---- hash function header -------------------------------------
        self.next_slide()
        self.play(
            keys_text.animate.scale(SUB_TITLES_SCALE).match_y(array_text),
            ht.keys.animate.move_to(keys_coords),
        )

        h_def = MathTex(r"h", r":U\rightarrow\left[m\right]").next_to(
            ht,
            UP,
            buff=HASH_TABLE_FUNCS_TITLE_BUFF,
        )
        h_def[0].set_color(FUNCS_COLOR)
        self.play(Write(h_def))

        # ---- two example arrows ---------------------------------------
        self.next_slide()
        x_1_text = (
            MathTex(r"h", r"\left(", "x_1", r"\right)", color=FUNCS_COLOR)
            .rotate(ht.arrows[0].get_angle())
            .next_to(ht.arrows[0], UP, buff=-0.5)
        )
        x_3_text = (
            MathTex(r"h", r"\left(", "x_3", r"\right)", color=FUNCS_COLOR)
            .rotate(ht.arrows[2].get_angle())
            .next_to(ht.arrows[2], UP, buff=-0.15)
        )
        x_1_text[-2].set_color(WHITE)
        x_3_text[-2].set_color(WHITE)
        self.play(Write(x_1_text), Write(ht.arrows[0]))
        self.next_slide()
        self.play(Write(x_3_text), Write(ht.arrows[2]))

        x_3_text.save_state()
        self.play(Unwrite(x_1_text), Unwrite(x_3_text))
        rest_arrows = VGroup(*[ht.arrows[i] for i in range(len(ht.arrows)) if i not in (0, 2)])
        self.play(
            TransformMatchingTex(h_def, hash_function_text),
            Write(rest_arrows),
        )

        # ---- note about O(1) -----------------------------------------
        self.next_slide()
        note = (
            Tex("Note: $h$ required to be computed in $O(1)$ time")
            .scale_to_fit_width(
                ht.width * 1.5,
            )
            .to_edge(LEFT + DOWN)
            .to_edge(DOWN, buff=0.2)
        )
        color_tex(note, {"h": FUNCS_COLOR}, tex_class=MathTex)
        self.play(Write(note))

        # ---- operations ----------------------------------------------
        self.next_slide()
        self.play(Unwrite(note))
        self.play(ht.arrows.animate.set_opacity(0.5))

        insert_text = get_func_text("Insert($x_3$)")
        search_text = get_func_text("Search($x_3$)")
        delete_text = get_func_text("Delete($x_3$)")
        for t in (insert_text, search_text, delete_text):
            compile_code_tex_line(t, t.text, bold_math=False)
            t[-2].set_color(SELECT_KEY_COLOR)
        operations = (
            VGroup(insert_text, search_text, delete_text)
            .arrange(DOWN)
            .next_to(keys_text, DOWN)
            .to_edge(LEFT)
        )
        self.play(
            AnimationGroup(
                *[Write(t) for t in operations],
                ht.keys[2].value_mob.animate.set_color(SELECT_KEY_COLOR),
                lag_ratio=0.5,
            ),
        )

        # ---- apply operations ----------------------------------------
        self.next_slide()
        x_3_text.restore()
        x_3_text[-2].set_color(SELECT_KEY_COLOR)
        self.play(ht.arrows[2].animate.set_opacity(1), Write(x_3_text))
        x_3_keys_text = ht.keys[2].value_mob.copy().set_z_index(20)
        self.play(
            x_3_keys_text.animate.scale(0.8).move_to(ht.array[ht.hash_func(2)]),
        )

        # ---- run-time brace ------------------------------------------
        self.next_slide()
        brace = BraceLabel(operations, "O(1)", RIGHT)
        self.play(Write(brace))

        # ---- U size question -----------------------------------------
        self.next_slide()
        self.play(
            Unwrite(x_3_keys_text),
            Unwrite(x_3_text),
            ht.arrows.animate.set_opacity(1),
            ht.keys[2].value_mob.animate.set_color(WHITE),
        )
        q1 = (
            Tex(r"What if $\left|U\right| \leq m$?")
            .next_to(brace, DOWN, buff=0.7)
            .set_x(
                -config.frame_width / 4,
            )
        )
        self.play(Write(q1))
        self.next_slide()
        q2 = Tex(r"What if $\left|U\right| > m$?").next_to(q1.get_left(), RIGHT, buff=0)
        self.play(TransformMatchingTex(q1, q2))

        # ---- chaining -----------------------------------------------
        self.next_slide(name="Chaining")
        chain_lbl = Text("Chaining!").scale(1.2).next_to(q2, DOWN)
        self.play(Write(chain_lbl))
        chains = ht.get_chaining()
        for lst in chains.values():
            self.play(
                AnimationGroup(*[FadeIn(c, shift=RIGHT, run_time=0.8) for c in lst], lag_ratio=0.2),
            )

        # ---- operations complexity ----------------------------------
        self.next_slide()
        x_i_texs = VGroup(
            *[
                MathTex("x_i", color=SELECT_KEY_COLOR)
                .match_width(operations[0][-2])
                .move_to(op[-2])
                for op in operations
            ]
        )
        self.play(
            Unwrite(brace),
            *[Transform(op[-2], x_i) for op, x_i in zip(operations, x_i_texs, strict=True)],
        )

        brace_avg = BraceLabel(
            operations[1:],
            r"O\left(\begin{matrix}\text{linked}\\\text{list's}\\\text{length}\end{matrix}\right)",
            RIGHT,
        )
        brace_avg.label.scale(0.6)
        brace_avg.brace.put_at_tip(brace_avg.label)
        insert_rt = (
            MathTex(r"O\left(1\right)").match_y(operations[0]).align_to(brace_avg.label, LEFT)
        )
        self.play(Write(insert_rt))
        self.next_slide()
        self.play(Write(brace_avg))

        # ---- expected length requirement ----------------------------
        self.next_slide()
        self.play(
            Unwrite(q2),
            Unwrite(chain_lbl),
            VGroup(operations, brace_avg, insert_rt).animate.align_to(array_text, UP),
        )
        ll_req = (
            Tex(
                r"If\ \  $\mathbb{E}\left[\begin{matrix}\text{linked}\\\text{list's}\\"
                r"\text{length}\end{matrix}\right]=O\left(1\right)$\ \  ",
                "then:",
            )
            .next_to(operations, DOWN, buff=0.2)
            .align_to(operations, LEFT)
        )
        self.play(Write(ll_req))

        # ---- medal --------------------------------------------------
        self.next_slide()
        medal = (
            SVGMobject(str(ASSETS / "best_ds_medal.svg"), stroke_color=WHITE, stroke_opacity=1)
            .scale(1)
            .next_to(ll_req[-1], DOWN, buff=0.2)
        )
        self.play(DrawBorderThenFill(medal, stroke_color=WHITE))

        # ---- exit ---------------------------------------------------
        self.next_slide()
        self.play(
            Unwrite(operations),
            Unwrite(brace_avg),
            Unwrite(insert_rt),
            Unwrite(ll_req),
            Unwrite(medal),
            Unwrite(title),
            *[Unwrite(c) for c in chains.values()],
        )
        self.wait()
