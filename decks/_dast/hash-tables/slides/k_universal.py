"""$k$-Universal Hash Families: stronger collision guarantee + 2-universal alt-perspective."""

from __future__ import annotations

from manim import (
    DOWN,
    GREEN,
    LEFT,
    RIGHT,
    TAU,
    UP,
    YELLOW,
    CurvedArrow,
    MathTex,
    Square,
    Tex,
    Text,
    Title,
    TransformMatchingShapes,
    Unwrite,
    VGroup,
    Write,
    config,
)

from simplex.engine.text import color_tex
from simplex.slides import BaseSlide

from utils import (
    DEFINITION_TEX_ENV,
    FUNCS_COLOR,
    K_UNIVERSAL_COLOR,
    PROB_BG_CELL_COLOR,
    SELECT_KEY_COLOR,
    animate_collision_prob,
    get_funcs_bowl,
    get_hash_family_table,
    get_hash_table_subtitles,
    get_main_hash_table_example,
    get_two_universal_def,
)


class KUniversalHashFamilies(BaseSlide):
    def construct(self) -> None:
        self.next_slide(name="k-Universal Hash Families")
        title = Title("$k$-Universal Hash Families")
        color_tex(title, {"k": K_UNIVERSAL_COLOR}, tex_class=MathTex)
        self.play(Write(title))

        frame_center, ht = get_main_hash_table_example(title)
        array_text, keys_text, hash_function_text = get_hash_table_subtitles(ht)
        hash_family_text = (
            Tex(r"hash family ($\mathcal{H}$)").match_y(array_text).set_x(-array_text.get_x())
        )
        hash_family = get_funcs_bowl().move_to(frame_center).match_x(hash_family_text)
        hash_family_text.match_height(keys_text)
        hash_family.scale(0.7)

        shift_recipe = DOWN * 0.6
        hash_family.shift(shift_recipe)
        ht.shift(shift_recipe)
        hash_function_text.shift(shift_recipe)

        select_arrow = CurvedArrow(
            hash_family.get_top() * RIGHT + ht.get_top() * UP,
            ht.get_top(),
            angle=-TAU / 6,
            color=GREEN,
            stroke_width=6,
        )
        select_text = MathTex("h", "_i", color=YELLOW).next_to(select_arrow, UP, buff=0.1)
        reminder = Text("Reminder:").next_to(title, DOWN, buff=0.5, aligned_edge=LEFT)
        hash_model = (
            VGroup(
                hash_family_text, keys_text, array_text, select_text, select_arrow, hash_family, ht
            )
            .scale(0.8)
            .next_to(reminder, DOWN, buff=0.5)
            .set_x(0)
        )
        self.play(Write(reminder), *map(Write, hash_model))

        # ---- k-universal definition --------------------------------
        self.next_slide()

        definition = Tex(
            r"""Let $k\in\mathbb{N}$ and let $\mathcal{H}$ be a family of hash functions $U\rightarrow\left[m\right]$. We say that $\mathcal{H}$ is $k$\textbf{-universal} if, when choosing $h$ randomly from $\mathcal{H}$:
            \[
            \begin{matrix}\mathbin{\forall}y_{1}\neq \ldots\neq y_{k}\in U\\
\mathbin{\forall}i_{1},\ldots,i_{k}\in\left[m\right]
\end{matrix},\
\underset{h\in\mathcal{H}}{\mathbb{P}}\left[h\left(y_{1}\right)=i_{1}\land\ldots\land h\left(y_{k}\right)=i_{k}\right]\leq\frac{1}{m^{k}}
            \]""",
            tex_environment=DEFINITION_TEX_ENV,
        ).next_to(title, DOWN, aligned_edge=LEFT)
        prob_eq_start = 96
        pure_prob_start = 125 - prob_eq_start
        prob_eq = definition[0][prob_eq_start:]
        prob_eq.scale_to_fit_width(config.frame_width * 0.9).next_to(
            definition[0][:prob_eq_start],
            DOWN,
            buff=0.3,
        ).set_x(0)
        color_tex(definition, {r"\textbf{-universal}": YELLOW}, tex_class=MathTex)
        color_tex(
            definition,
            {
                "y_{1}": SELECT_KEY_COLOR,
                "y_{k}": SELECT_KEY_COLOR,
                "h": FUNCS_COLOR,
                "k": K_UNIVERSAL_COLOR,
            },
            tex_class=MathTex,
        )
        definition[0][-1].set_color(K_UNIVERSAL_COLOR)
        whole_family = VGroup(ht, select_arrow, select_text, hash_family)
        self.play(
            Unwrite(array_text),
            Unwrite(keys_text),
            Unwrite(hash_family_text),
            Unwrite(reminder),
            whole_family.animate.scale_to_fit_height(
                (config.frame_height / 2 + definition.get_bottom()[1]) * 0.9,
            ).to_edge(DOWN, buff=0.3),
        )
        self.play(Write(definition))

        # ---- compress to just the probability inequality -----------
        self.next_slide()
        self.region.update(top=title)
        self.play(Unwrite(whole_family), Unwrite(definition[0][:prob_eq_start]))
        self.play(
            VGroup(prob_eq[:pure_prob_start], prob_eq[pure_prob_start:])
            .animate.scale(1.3)
            .arrange(DOWN)
            .move_to(self.region.center),
        )

        # ---- 2-universal definition --------------------------------
        self.next_slide()
        array_size = ht.array_size
        keys_size = ht.keys_size
        self.region.update(top=title)
        frame_center = self.region.center
        hashs_tab = get_hash_family_table(array_size, keys_size, seed=2).set_y(frame_center[1])
        self.region.update(left=hashs_tab, top=title)
        frame_center = self.region.center

        two_universal_def = get_two_universal_def()
        two_universal_def.match_width(prob_eq).move_to(prob_eq)
        self.play(TransformMatchingShapes(prob_eq, two_universal_def))

        # ---- alt perspective ---------------------------------------
        self.next_slide()
        self.play(
            two_universal_def.animate.scale(0.7)
            .next_to(title, DOWN, buff=0.5)
            .set_x(frame_center[0]),
        )
        self.play(Write(hashs_tab))

        # ---- examples setup ----------------------------------------
        self.next_slide()
        down_buff = 0.4
        down_arrow = (
            Tex(r"$\Downarrow$").scale(1.3).next_to(two_universal_def, DOWN, buff=down_buff)
        )
        for_x_y = Tex(r"for ", "$y_1=$", "$x_1$", ", ", "$y_2=$", "$x_2$", r"\ \ :").next_to(
            down_arrow,
            DOWN,
            buff=down_buff,
        )
        first_key = for_x_y[2].set_color(SELECT_KEY_COLOR)
        second_key = for_x_y[5].set_color(SELECT_KEY_COLOR)

        for_i = Tex(r"for ", "$i_1=$", "$3$", " , ", "$i_2=$", "$2$", r"\ \ :").next_to(
            for_x_y, DOWN
        )
        first_i = for_i[2]
        second_i = for_i[5]

        alt_def = MathTex(
            r"\mathbb{P}\left[\begin{matrix}\hspace{1cm}\\\hspace{1cm}\end{matrix}\right]\leq\frac{1}{m^{2}}",
        ).next_to(for_i, DOWN)
        prob_paren = alt_def[0][1:3]
        prob_sq = (
            Square(stroke_color=GREEN, fill_color=PROB_BG_CELL_COLOR, fill_opacity=1)
            .match_height(prob_paren)
            .scale(0.9)
            .move_to(prob_paren)
        )
        for_x_y.align_to(two_universal_def, LEFT)
        for_i.next_to(for_x_y, DOWN, aligned_edge=LEFT, buff=0.2).shift(RIGHT * 0.5)
        self.play(Write(down_arrow))
        self.play(Write(for_x_y), Write(for_i), Write(alt_def), Write(prob_sq))

        # ---- first example -----------------------------------------
        self.next_slide()
        bg_cells = VGroup(
            *[
                VGroup(
                    *[
                        hashs_tab.get_highlighted_cell(
                            (j, i),
                            color=PROB_BG_CELL_COLOR,
                            fill_opacity=0,
                            z_index=-20,
                        )
                        for i in range(1, hashs_tab.row_dim + 1)
                    ]
                )
                for j in range(1, hashs_tab.col_dim + 1)
            ]
        )
        self.play(*animate_collision_prob(0, 1, hashs_tab, bg_cells, i_1=2, i_2=1))

        # ---- iterate over (y_1, y_2, i_1, i_2) ----------------------
        self.next_slide()
        LAST_IDX = r"\left|U\right|"
        first = True
        for y_1 in range(keys_size):
            for y_2 in range(y_1 + 1, keys_size):
                if y_1 == keys_size - 2 or y_2 == keys_size - 2:
                    continue
                for i_1 in range(array_size):
                    for i_2 in range(array_size):
                        if i_1 == array_size - 2 or i_2 == array_size - 2:
                            continue
                        anims = animate_collision_prob(
                            y_1, y_2, hashs_tab, bg_cells, i_1=i_1, i_2=i_2
                        )
                        new_y1 = (
                            MathTex(
                                rf"x_{{{LAST_IDX if y_1 == keys_size - 1 else y_1 + 1}}}",
                                color=SELECT_KEY_COLOR,
                            )
                            .move_to(first_key)
                            .align_to(first_key, LEFT)
                        )
                        new_y2 = (
                            MathTex(
                                rf"x_{{{LAST_IDX if y_2 == keys_size - 1 else y_2 + 1}}}",
                                color=SELECT_KEY_COLOR,
                            )
                            .move_to(second_key)
                            .align_to(second_key, LEFT + UP)
                        )
                        new_i1 = (
                            MathTex(
                                str(i_1 + 1) if i_1 != array_size - 1 else "m",
                            )
                            .move_to(first_i)
                            .align_to(first_i, LEFT)
                        )
                        new_i2 = (
                            MathTex(
                                str(i_2 + 1) if i_2 != array_size - 1 else "m",
                            )
                            .move_to(second_i)
                            .align_to(second_i, LEFT)
                        )
                        self.play(
                            *anims,
                            TransformMatchingShapes(first_key, new_y1),
                            TransformMatchingShapes(second_key, new_y2),
                            TransformMatchingShapes(first_i, new_i1),
                            TransformMatchingShapes(second_i, new_i2),
                            run_time=0.02 if not first else 1,
                        )
                        first_key, second_key, first_i, second_i = new_y1, new_y2, new_i1, new_i2
                        if first:
                            self.next_slide()
                            first = False

        # ---- exit --------------------------------------------------
        self.next_slide()
        to_unwrite = [
            down_arrow,
            for_x_y,
            for_i,
            alt_def,
            prob_sq,
            first_key,
            second_key,
            first_i,
            second_i,
            two_universal_def,
            bg_cells,
        ]
        self.play(*[Unwrite(o) for o in to_unwrite])
        self.wait()
