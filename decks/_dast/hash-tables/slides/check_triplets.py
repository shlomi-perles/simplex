"""Check Triplets: detect an arithmetic triplet in $O(n^2)$ expected time."""

from __future__ import annotations

from typing import ClassVar

from manim import (
    BLUE,
    DOWN,
    DR,
    LEFT,
    RIGHT,
    UP,
    YELLOW,
    BulletedList,
    Indicate,
    MathTex,
    Tex,
    Text,
    Title,
    Unwrite,
    VGroup,
    Write,
    config,
)

from simplex.engine.text import color_tex
from simplex.mobjects import ArrayMob, ArrayPointer
from simplex.slides import BaseSlide

from utils import DEFINITION_TEX_ENV, get_func_text


# dastimator's REMOVE_MATH_SPACE_PREAMBLE: simplex's SIMPLEX_DARK theme
# already injects an equivalent preamble globally, so the per-call value
# can be empty.
REMOVE_MATH_SPACE = ""


class CheckTriplets(BaseSlide):
    example_lst: ClassVar[list[int]] = [5, 9, 4, 1, 2]

    def construct(self) -> None:
        self.next_slide(name="Question - Check Triplets")
        self.title = Title("Check Triplets")
        self.play(Write(self.title))
        self._show_question()
        self._show_solution()
        self.wait()

    def _show_question(self) -> None:
        question = (
            BulletedList(
                r"\textbf{Algorithm:}",
                r"\textbf{Input:} Array $A$ of n integers.",
                REMOVE_MATH_SPACE
                + r"\textbf{Output:} Determine if there exists a triplet forming an arithmetic"
                r" sequence of length $3$: \[\exists d\ s.t.\ \forall i\ \ a_{i+1}-a_{i}=d\]",
                "If such a triplet exists, return it.",
                r"\textbf{Expected Runtime:} $O\left(n^{2}\right)$",
                tex_environment=DEFINITION_TEX_ENV,
                dot_scale_factor=3,
                buff=0.18,
            )
            .scale(0.8)
            .next_to(self.title, DOWN)
            .align_to(self.title, LEFT)
        )
        color_tex(question, {"A": BLUE}, tex_class=MathTex)
        question_func = (
            get_func_text("CheckTriplets(A)", ["A"])
            .match_height(question[0])
            .next_to(question[0], RIGHT)
        )
        self.play(Write(question), Write(question_func))

        # ---- example ------------------------------------------------
        self.next_slide()
        example = (
            Tex("Example:").scale(1.2).next_to(question, DOWN, buff=0.4).align_to(question, LEFT)
        )
        arr = ArrayMob("A=", *[str(v) for v in self.example_lst]).match_height(example)
        arr.name_mob[0][0].set_color(BLUE)
        func_call = question_func.copy().match_height(arr.name_mob)
        sol = MathTex(r"= [1, 5, 9]")
        color_tex(sol, {"1": YELLOW, "5": YELLOW, "9": YELLOW}, tex_class=MathTex)
        sol[0][-4].set_color(YELLOW)

        self.region.update(top=example)
        VGroup(arr, func_call, sol).arrange(RIGHT).scale_to_fit_width(
            config.frame_width * 0.9,
        ).move_to(self.region.center)
        self.play(Write(VGroup(example, arr)))

        # ---- solution ---------------------------------------------
        self.next_slide()
        self.play(
            Write(VGroup(func_call, sol)),
            *[arr.get_entry(i).value_mob.animate(run_time=2).set_color(YELLOW) for i in (0, 1, 3)],
        )

        # ---- exit example -----------------------------------------
        self.next_slide()
        self.play(Unwrite(VGroup(example, question, func_call, arr, sol, question_func)))

    def _show_solution(self) -> None:
        self.next_slide(name="Solution - Check Triplets")
        subtitle = Text("Solution").scale(1.2).next_to(self.title, DOWN).align_to(self.title, LEFT)
        self.play(Write(subtitle))

        naive_title = (
            Text("Naive Solution")
            .scale(0.8)
            .next_to(subtitle, DOWN, buff=0.5)
            .align_to(subtitle, LEFT)
        )
        naive = (
            BulletedList(
                r"Use three nested loops to check all possible triplets.",
                r"\textbf{Runtime:} $O\left(n^{3}\right)$",
                tex_environment=DEFINITION_TEX_ENV,
                dot_scale_factor=3,
                buff=0.18,
            )
            .next_to(naive_title, DOWN)
            .align_to(naive_title, LEFT)
        )
        self.play(Write(VGroup(naive_title, naive[:-1])))

        self.next_slide()
        self.play(Write(naive[-1]))

        # ---- observation ------------------------------------------
        self.next_slide()
        self.play(Unwrite(VGroup(naive_title, naive)))

        observation_title = (
            Text("Observation")
            .scale(0.8)
            .next_to(subtitle, DOWN, buff=0.5)
            .align_to(subtitle, LEFT)
        )
        observation = (
            BulletedList(
                REMOVE_MATH_SPACE
                + r"An arithmetic sequence of length $3$ is determined by its first two elements:"
                + r"\[\begin{matrix}1)\ b-a=d\\2)\ c-b=d\end{matrix}\overset{2-1}{\Longrightarrow}"
                r"c=b+\left(b-a\right)=2b-a\]",
                r"Thus, for each $a, b$ pair, we can check if $2b-a$ exists in $A$ (or even better,"
                r" in a hash table!).",
                tex_environment=DEFINITION_TEX_ENV,
                dot_scale_factor=3,
                buff=0.4,
            )
            .next_to(naive_title, DOWN)
            .align_to(naive_title, LEFT)
        )
        color_tex(
            observation, {"a": YELLOW, "b": YELLOW, "c": YELLOW, "A": BLUE}, tex_class=MathTex
        )
        self.play(Write(VGroup(observation_title, observation[:-1])))

        self.next_slide()
        self.play(Write(observation[-1]))

        # ---- algorithm steps --------------------------------------
        self.next_slide()
        self.play(Unwrite(VGroup(observation_title, observation)))
        steps = (
            BulletedList(
                r"Initialize hash table $T$ and insert all elements of $A$.",
                r"For each $a<b$ pair, check if $2b-a$ exists in $T$.",
                r"\textbf{Expected Runtime:}",
                tex_environment=DEFINITION_TEX_ENV,
                dot_scale_factor=3,
                buff=0.4,
            )
            .next_to(subtitle, DOWN)
            .align_to(subtitle, LEFT)
        )
        color_tex(steps, {"a": YELLOW, "b": YELLOW, "A": BLUE}, tex_class=MathTex)
        self.play(Write(steps[:-1]))

        example = (
            Tex("Example:").scale(1.2).next_to(steps[:-1], DOWN, buff=0.4).align_to(steps, LEFT)
        )
        self.region.update(top=example)
        arr = (
            ArrayMob("A=", *[str(v) for v in self.example_lst])
            .scale_to_fit_width(config.frame_width * 0.4)
            .move_to(self.region.center)
            .align_to(example, LEFT)
        )
        arr.name_mob[0][0].set_color(BLUE)
        hash_arr = ArrayMob("T", *[str(v) for v in self.example_lst]).match_height(arr)
        hash_arr.entries.arrange(DOWN, buff=0)
        hash_arr.name_mob.next_to(hash_arr.entries, UP, buff=0.2)
        hash_arr.to_edge(DR)
        self.play(Write(VGroup(example, arr)))

        p1 = ArrayPointer(arr, 0, text="a", direction=0.4 * DOWN)
        p2 = ArrayPointer(arr, 1, text="b", direction=0.4 * DOWN)
        self.play(Write(hash_arr))
        self.play(Write(p1), Write(p2), arr.indicate_at(0), arr.indicate_at(1))

        # ---- first calc ------------------------------------------
        self.next_slide()
        c = str(2 * self.example_lst[1] - self.example_lst[0])
        self.region.update(right=hash_arr.entries, left=arr.entries)
        calc = MathTex("2b-a=", c).next_to(example, DOWN).set_x(self.region.center[0])
        color_tex(calc, {"a": YELLOW, "b": YELLOW, c: BLUE}, tex_class=MathTex)
        self.play(Write(calc))
        func_calc = get_func_text(f"T.Search({c})", [c]).next_to(calc, DOWN, buff=1.3)
        self.play(Write(func_calc))

        for a_idx, a in enumerate(self.example_lst):
            found = False
            for b_idx, b in enumerate(self.example_lst):
                if a >= b or (a_idx == 0 and b_idx == 1):
                    continue
                self.next_slide()
                c = str(2 * b - a)
                self.play(p1.to_entry(a_idx), run_time=0.3)
                self.play(p2.to_entry(b_idx), run_time=0.3)
                anims = [
                    calc[1].animate.become(MathTex(c, color=BLUE).move_to(calc[1])),
                ]
                arg = func_calc[-3:-1]
                anims.append(
                    arg.animate.become(get_func_text(f"{c}", [c]).match_height(arg).move_to(arg)),
                )
                self.play(*anims, run_time=0.7)
                if int(c) in self.example_lst:
                    found = True
                    self.play(hash_arr.indicate_at(self.example_lst.index(int(c))))
                    break
            if found:
                break

        # ---- complexity -------------------------------------------
        self.next_slide()
        self.play(Unwrite(VGroup(calc, func_calc, p1, p2, arr, hash_arr, example)))
        self.play(Write(steps[-1]))

        self.next_slide()
        complexity = MathTex(
            r"O\left(n\right)",
            r"+O_{\mathbb{E}}\left(n^{2}\right)",
            r"=O_{\mathbb{E}}\left(n^{2}\right)",
        ).next_to(steps[-1], RIGHT)
        self.play(Write(complexity[0]), steps[1].animate.set_opacity(0.5), Indicate(steps[0]))

        self.next_slide()
        steps[1].set_opacity(1)
        self.play(Write(complexity[1]), steps[0].animate.set_opacity(0.5), Indicate(steps[1]))

        self.next_slide()
        self.play(Write(complexity[2]), steps.animate.set_opacity(1))

        # ---- exit --------------------------------------------------
        self.next_slide()
        self.play(Unwrite(VGroup(self.title, subtitle, steps, complexity)))
