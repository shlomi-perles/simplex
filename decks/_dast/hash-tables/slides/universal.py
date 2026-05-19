"""Universal Hash Families -- definition + alternative probability view."""

from __future__ import annotations

import numpy as np
from manim import (
    DOWN,
    LEFT,
    RIGHT,
    TAU,
    UP,
    CurvedArrow,
    GREEN,
    MathTex,
    Square,
    Tex,
    Title,
    TransformMatchingShapes,
    TransformMatchingTex,
    Unwrite,
    VGroup,
    Write,
    YELLOW,
    config,
)

from simplex.engine.text import color_tex
from simplex.slides import BaseSlide

from utils import (
    DEFINITION_TEX_ENV,
    FUNCS_COLOR,
    PROB_BG_CELL_COLOR,
    SELECT_KEY_COLOR,
    animate_collision_prob,
    get_funcs_bowl,
    get_hash_family_table,
    get_hash_table_subtitles,
    get_main_hash_table_example,
)


class UniversalHashFamilies(BaseSlide):
    def construct(self) -> None:
        np.random.seed(0)
        title = Title("Universal Hash Families")
        frame_center, ht = get_main_hash_table_example(title)
        array_text, keys_text, hash_function_text = get_hash_table_subtitles(ht)
        keys_text.match_y(array_text)

        self.next_slide(name="Universal Hash Families")
        self.add(ht, array_text, keys_text, hash_function_text)
        self.play(Write(title))

        hash_family_text = (
            Tex(r"hash family ($\mathcal{H}$)")
            .match_y(array_text)
            .set_x(-array_text.get_x())
        )
        hash_family = get_funcs_bowl().move_to(frame_center).match_x(hash_family_text)
        self.play(Write(hash_family_text))
        self.play(Write(hash_family))

        # ---- shrink family + add a select arrow ----------------------
        self.next_slide()
        self.play(
            hash_family_text.animate.match_height(keys_text),
            hash_family.animate.scale(0.7),
        )

        shift_down = DOWN * 0.6
        self.play(
            hash_family.animate.shift(shift_down),
            ht.animate.shift(shift_down),
            hash_function_text.animate.shift(shift_down),
        )

        select_arrow = CurvedArrow(
            hash_family.get_top() * RIGHT + ht.get_top() * UP,
            ht.get_top(),
            angle=-TAU / 6,
            color=GREEN,
            stroke_width=6,
        )
        select_text = MathTex("h", "_i", color=YELLOW).next_to(select_arrow, UP, buff=0.1)
        select_text.save_state()
        self.play(Write(select_arrow), TransformMatchingTex(hash_function_text, select_text))

        # ---- cycle through 7 different hashes ------------------------
        self.next_slide()
        prev = select_text
        for i in range(1, 8):
            new_text = MathTex("h", rf"_{{{i}}}", color=YELLOW).next_to(select_arrow, UP, buff=0.1)
            self.play(
                TransformMatchingTex(prev, new_text),
                ht.animate.rehash(lambda _i: np.random.randint(0, 5)),
            )
            prev = new_text

        # ---- universal hash family definition ------------------------
        self.next_slide()
        definition = Tex(
            r"""Let $\mathcal{H}$ be a family of hash functions $U\rightarrow\left[m\right]$. We say that $\mathcal{H}$ is \textbf{universal} if, when choosing $h$ randomly from $\mathcal{H}$:
            \[
            \forall x\neq y\in U,\underset{h\in\mathcal{H}}{\mathbb{P}}\left[h\left(x\right)=h\left(y\right)\right]\leq\frac{1}{m}
            \]""",
            tex_environment=DEFINITION_TEX_ENV,
        ).next_to(title, DOWN)
        prob_eq_start = 85
        prob_eq = definition[0][prob_eq_start:]
        prob_eq.next_to(definition[0][:prob_eq_start], DOWN, buff=0)
        color_tex(definition, {r"\textbf{universal}": YELLOW}, tex_class=MathTex)
        color_tex(
            definition,
            {"x": SELECT_KEY_COLOR, "y": SELECT_KEY_COLOR, "h": FUNCS_COLOR},
            tex_class=MathTex,
        )

        select_text.restore().move_to(prev)
        self.play(TransformMatchingTex(prev, select_text))

        whole_family = VGroup(ht, select_arrow, select_text, hash_family)
        self.play(
            Unwrite(array_text),
            Unwrite(keys_text),
            Unwrite(hash_family_text),
            whole_family.animate.scale_to_fit_height(
                (config.frame_height / 2 - definition.get_bottom()[1]) * 0.8,
            ).to_edge(DOWN, buff=0.3),
        )
        self.play(Write(definition))

        # ---- events map perspective ---------------------------------
        self.next_slide()
        self.region.update(top=title)
        frame_center = self.region.center
        array_size = ht.array_size
        keys_size = ht.keys_size
        hashs_tab = get_hash_family_table(array_size, keys_size).set_y(frame_center[1])
        self.region.update(left=hashs_tab, top=title)
        frame_center = self.region.center

        self.play(Unwrite(whole_family), Unwrite(definition[0][:prob_eq_start]))
        self.play(
            prob_eq.animate.scale(0.9)
            .next_to(title, DOWN, buff=1.2)
            .set_x(frame_center[0]),
        )
        self.play(Write(hashs_tab))

        # ---- alternative probability perspective --------------------
        self.next_slide()
        down_buff = 0.6
        down_arrow = Tex(r"$\Downarrow$").scale(1.3).next_to(prob_eq, DOWN, buff=down_buff)
        for_x_y = Tex(r"for ", "$x_1$", ", ", "$x_4$", "\\ \\ :").next_to(
            down_arrow, DOWN, buff=down_buff,
        )
        first_key = for_x_y[1].set_color(SELECT_KEY_COLOR)
        second_key = for_x_y[3].set_color(SELECT_KEY_COLOR)
        color_tex(
            for_x_y,
            {"x_1": SELECT_KEY_COLOR, "x_4": SELECT_KEY_COLOR},
            tex_class=MathTex,
        )
        alt_def = MathTex(
            r"\mathbb{P}\left[\begin{matrix}\hspace{1cm}\\\hspace{1cm}"
            r"\end{matrix}\right]\leq\frac{1}{m}",
        ).next_to(for_x_y, DOWN)
        prob_paren = alt_def[0][1:3]
        prob_sq = (
            Square(stroke_color=GREEN, fill_color=PROB_BG_CELL_COLOR, fill_opacity=1)
            .match_height(prob_paren)
            .scale(0.9)
            .move_to(prob_paren)
        )
        for_x_y.align_to(prob_eq, LEFT)
        self.play(Write(down_arrow))
        self.play(Write(for_x_y), Write(alt_def), Write(prob_sq))

        # ---- first collision example --------------------------------
        self.next_slide()
        bg_cells = VGroup(
            *[
                VGroup(
                    *[
                        hashs_tab.get_highlighted_cell(
                            (j, i), color=PROB_BG_CELL_COLOR, fill_opacity=0, z_index=-20,
                        )
                        for i in range(1, hashs_tab.row_dim + 1)
                    ]
                )
                for j in range(1, hashs_tab.col_dim + 1)
            ]
        )
        self.play(*animate_collision_prob(0, 3, hashs_tab, bg_cells))

        # ---- cycle all (i, j) pairs ----------------------------------
        self.next_slide()
        LAST_IDX = r"\left|U\right|"
        first = True
        for i in range(keys_size):
            for j in range(i + 1, keys_size):
                if i == keys_size - 2 or j == keys_size - 2:
                    continue
                anims = animate_collision_prob(i, j, hashs_tab, bg_cells)
                new_first = (
                    MathTex(rf"x_{{{LAST_IDX if i == keys_size - 1 else i + 1}}}", color=SELECT_KEY_COLOR)
                    .move_to(first_key)
                    .align_to(first_key, LEFT)
                )
                new_second = (
                    MathTex(rf"x_{{{LAST_IDX if j == keys_size - 1 else j + 1}}}", color=SELECT_KEY_COLOR)
                    .move_to(second_key)
                    .align_to(second_key, LEFT + UP)
                )
                self.play(
                    *anims,
                    TransformMatchingShapes(first_key, new_first),
                    TransformMatchingShapes(second_key, new_second),
                )
                first_key = new_first
                second_key = new_second
                if first:
                    self.next_slide()
                    first = False

        # ---- exit ---------------------------------------------------
        self.next_slide()
        self.play(
            *[
                Unwrite(o)
                for o in (down_arrow, for_x_y, alt_def, prob_sq, first_key, second_key,
                         title, hashs_tab, prob_eq, bg_cells)
            ],
        )
        self.wait()
