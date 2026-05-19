"""Theorem: every 2-universal hash family is also universal.

Builds an alternative-perspective picture (partition by collision value), then
walks a textbook union-bound proof line by line.
"""

from __future__ import annotations

from manim import (
    BLUE_C,
    DOWN,
    GOLD_C,
    GREEN,
    LEFT,
    MAROON_C,
    PURPLE_C,
    RED_C,
    RIGHT,
    UP,
    BraceLabel,
    Line,
    MathTex,
    Square,
    Tex,
    Title,
    Unwrite,
    VGroup,
    Write,
    config,
)

from simplex.engine.text import color_tex
from simplex.slides import BaseSlide

from utils import (
    FUNCS_COLOR,
    K_UNIVERSAL_COLOR,
    PROB_BG_CELL_COLOR,
    SELECT_KEY_COLOR,
    animate_collision_prob,
    get_hash_family_table,
    get_two_universal_def,
    get_unit_bound,
    get_universal_hash_family_def,
)


class TwoUniversalsAreUniversal(BaseSlide):
    def construct(self) -> None:
        self.next_slide(name="2-Universals Are Universal")

        self.title = Title("$k$-Universal Hash Families")
        color_tex(self.title, {"k": K_UNIVERSAL_COLOR}, tex_class=MathTex)
        self.region.update(top=self.title)
        array_size = 5
        keys_size = 6
        self.hashs_tab = get_hash_family_table(array_size, keys_size, seed=2).set_y(self.region.center[1])
        self.add(self.title, self.hashs_tab)

        self.region.update(top=self.title, left=self.hashs_tab)
        theorem = Tex(
            r"Theorem:\\If $\mathcal{H}$ is a $2$-universal hash family, then it is also universal.",
            tex_environment="{minipage}{5cm}",
        ).move_to(self.region.center)
        color_tex(theorem, {"2": K_UNIVERSAL_COLOR, r"\mathcal{H}": FUNCS_COLOR}, tex_class=MathTex)
        self.play(Write(theorem))

        self.next_slide()
        self.play(Unwrite(theorem))
        self._play_alternative_perspective()
        self.next_slide()
        self._play_proof()

    # --------------------------------------------------------- perspective
    def _play_alternative_perspective(self) -> None:
        universal_def = get_universal_hash_family_def()
        two_universal_def = get_two_universal_def()
        self.region.update(top=self.title, left=self.hashs_tab)
        partition_line = (
            Line(LEFT, RIGHT)
            .scale_to_fit_width(0.9 * (config.frame_width / 2 - self.hashs_tab.get_right()[0]))
            .move_to(self.region.center)
        )
        down_arrow = Tex(r"$\Downarrow$").scale(1.3).move_to(partition_line)

        self.region.update(top=self.title, left=self.hashs_tab, bottom=partition_line)
        two_universal_def.move_to(self.region.center)
        self.region.update(top=partition_line, left=self.hashs_tab, bottom=-config.frame_height / 2, right=config.frame_width / 2)
        universal_def.move_to(self.region.center)

        self.play(*map(Write, [universal_def, two_universal_def, down_arrow]))

        # ---- swap to alternative formulation -----------------------
        self.next_slide()
        self.play(Unwrite(down_arrow), Unwrite(two_universal_def))
        self.play(Write(partition_line))

        single_probs = MathTex(
            *[
                rf"\mathbb{{P}}[h\left(x_{{1}}\right)=h\left(x_{{3}}\right)={i if i != 4 else 'm'}]"
                if i != 3 else r"\ldots"
                for i in range(5)
            ],
            arg_separator="+",
        ).match_width(partition_line).align_to(self.hashs_tab, UP).match_x(partition_line)
        color_tex(
            single_probs,
            {"h": FUNCS_COLOR, "x_{1}": SELECT_KEY_COLOR, "x_{3}": SELECT_KEY_COLOR},
            tex_class=MathTex,
        )
        self.play(Write(single_probs))

        alt_def = MathTex(
            *[r"\mathbb{P}\left[\begin{matrix}\hspace{1cm}\\\hspace{1cm}\end{matrix}\right]"] * len(single_probs),
            arg_separator="+",
        )
        alt_def.match_width(single_probs).next_to(single_probs, DOWN, buff=0.35)

        colors = [RED_C, BLUE_C, GOLD_C, MAROON_C, PURPLE_C]
        prob_paren = alt_def[0][1:3]
        prob_squares = VGroup(
            *[
                Square(color=colors[i], fill_opacity=0.6)
                .match_height(prob_paren).scale(0.9).move_to(alt_def[i][1:3])
                for i in range(len(alt_def))
            ]
        )

        self.play(Write(alt_def), Write(prob_squares))

        bg_cells = VGroup(
            *[
                VGroup(
                    *[
                        self.hashs_tab.get_highlighted_cell(
                            (j, i), color=PROB_BG_CELL_COLOR, fill_opacity=0, z_index=-20,
                        )
                        for i in range(1, 5)
                    ]
                )
                for j in range(1, 5)
            ]
        )
        self.play(
            *[
                anim
                for i in range(5)
                for anim in animate_collision_prob(
                    0, 2, self.hashs_tab, bg_cells, i, i,
                    cell_color=colors[i], cells_opacity=0.6, change_others_opacity=False,
                )
            ]
        )

        # ---- bracket each term ------------------------------------
        self.next_slide()
        brackets = VGroup(
            *[
                BraceLabel(alt_def[i][1:3], r"\leq\frac{1}{m^2}", DOWN, font_size=20, buff=0.02)
                for i in range(len(prob_squares))
            ]
        )
        for brace in brackets:
            brace.brace.put_at_tip(brace.label, buff=0.05)
        first_write = 2
        self.play(Write(brackets[first_write]))

        self.next_slide()
        self.play(*[Write(brackets[i]) for i in range(len(brackets)) if i != first_write])

        # ---- final bracket ----------------------------------------
        self.next_slide()
        total = BraceLabel(brackets, r"\leq\frac{1}{m}", DOWN, font_size=30, buff=0.05)
        total.brace.put_at_tip(total.label, buff=0.1)
        self.play(Write(total))
        self.play(universal_def.animate.next_to(partition_line, DOWN, buff=0.2))

        # ---- final result -----------------------------------------
        self.next_slide()
        univ_alt = MathTex(
            r"\mathbb{P}\left[\begin{matrix}\hspace{1cm}\\\hspace{1cm}\end{matrix}\right]\leq\frac{1}{m}",
        )
        univ_paren = univ_alt[0][1:3]
        univ_sq = (
            Square(stroke_color=GREEN, fill_color=PROB_BG_CELL_COLOR, fill_opacity=1)
            .match_height(univ_paren).scale(0.9).move_to(univ_paren)
        )
        self.region.update(top=universal_def, left=self.hashs_tab)
        univ_group = VGroup(univ_alt, univ_sq).move_to(self.region.center)
        self.play(
            *animate_collision_prob(0, 2, self.hashs_tab, bg_cells),
            Write(univ_group),
        )

        # ---- exit perspective --------------------------------------
        self.next_slide()
        self.play(
            *map(Unwrite, [
                self.hashs_tab, bg_cells, partition_line, universal_def, single_probs,
                alt_def, prob_squares, brackets, total, univ_group,
            ]),
        )

    # ------------------------------------------------------------ proof
    def _play_proof(self) -> None:
        assumption = Tex(r"Assume $\mathcal{H}$ is $2$-universal:").next_to(
            self.title, DOWN, buff=0.5,
        ).align_to(self.title, LEFT)
        self.play(Write(assumption))

        # ---- write derivation --------------------------------------
        self.next_slide()
        proof = VGroup(
            MathTex(
                r"\mathbb{P}\left[h\left(x\right)=h\left(y\right)\right]",
                r"=\mathbb{P}\left[\left(h\left(x\right)=h\left(y\right)=1\right)"
                r"\lor\ldots\lor\left(h\left(x\right)=h\left(y\right)=m\right)\right]",
            ),
            MathTex(
                r"\leq\sum_{i=1}^{m}\mathbb{P}\left[h\left(x\right)=h\left(y\right)=i\right]",
            ),
            MathTex(
                r"\leq\sum_{i=1}^{m}\frac{1}{m^{2}}",
                r"=\frac{1}{m}",
            ),
        ).arrange(DOWN, buff=0.6).scale_to_fit_width(config.frame_width * 0.9)

        for i, line in enumerate(proof):
            color_tex(line, {"x": SELECT_KEY_COLOR, "y": SELECT_KEY_COLOR, "h": FUNCS_COLOR}, tex_class=MathTex)
            if i != 0:
                line.align_to(proof[0][1], LEFT)

        self.region.update(top=assumption)
        proof.move_to(self.region.center).align_to(assumption, LEFT)

        self.region.update(left=proof[0][0], top=proof[0][0], bottom=proof[-1][-1], right=proof[-1][-1])
        vdots = MathTex(r"\vdots").scale(3).move_to(self.region.center)
        self.play(Write(proof[0][0]), Write(vdots), Write(proof[-1][-1]))

        steps = VGroup(proof[0][1], *proof[1:-1], proof[-1][0])
        self.next_slide()
        self.play(Unwrite(vdots))
        self.play(Write(steps[0]))

        union_bound = get_unit_bound().scale_to_fit_width(
            (config.frame_width / 2 + steps[1].get_left()[0]) * 0.6,
        ).next_to(steps[1], LEFT, buff=0.6)
        union_bound += Tex("Union Bound").match_width(union_bound).scale(0.5).next_to(
            union_bound, UP, buff=0.1, aligned_edge=LEFT,
        )
        for i, step in enumerate(steps[1:], start=1):
            self.next_slide()
            if i == 1:
                self.play(Write(step), Write(union_bound))
            else:
                self.play(Write(step))

        # ---- exit --------------------------------------------------
        self.next_slide()
        self.play(*map(Unwrite, [self.title, assumption, proof, union_bound]))
        self.wait()
