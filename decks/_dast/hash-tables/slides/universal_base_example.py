"""Universal Hash Families - Example 3: $h_a(x) = \\sum a_i x_i \\pmod p$.

Three acts:
1. Bases intro -- counting in different bases up to 143, then base-conversion.
2. Example explanation -- $p, k$ values + a concrete $U$ + a working example.
3. Proof that this family is universal.
"""

from __future__ import annotations

from manim import (
    BLUE,
    DL,
    DOWN,
    DR,
    LEFT,
    RED,
    RIGHT,
    TAU,
    UP,
    Arrow,
    CurvedArrow,
    FadeIn,
    GREEN,
    MathTex,
    ReplacementTransform,
    Tex,
    Text,
    Title,
    TransformMatchingShapes,
    TransformMatchingTex,
    Unwrite,
    VGroup,
    WHITE,
    Write,
    YELLOW,
    config,
)

from simplex.engine.text import color_tex
from simplex.slides import BaseSlide

from hash_table import HashTable
from utils import (
    DEFINITION_TEX_ENV,
    FUNCS_COLOR,
    K_UNIVERSAL_COLOR,
    SELECT_KEY_COLOR,
    Count,
    IntegerBase,
    get_base_convert_calc,
    get_funcs_bowl,
    get_hash_func,
    get_hash_func_calc,
    get_univ_def_reminder,
)


class UniversalHashBaseExample(BaseSlide):
    numbers_color = BLUE
    bases_color = RED
    k_color = K_UNIVERSAL_COLOR

    def construct(self) -> None:
        self.next_slide(name="Universal Hash Families Example 3")
        self.title = Title("Universal Hash Families - Example ", "3")
        self.play(Write(self.title))

        self._bases_intro()
        self._explain_example()
        self._proof_of_universal_hash_family()

        self.wait()

    # ---------------------------------------------------------------- bases
    def _bases_intro(self) -> None:
        sub_title = Text("Introduction to Base Changing").scale(0.8).next_to(self.title, DOWN)

        base_values = [2, 4, 6, 8, 10, 16]
        bases = VGroup(
            *[
                VGroup(
                    Tex("Base ", f"{b}", ":"),
                    IntegerBase(0, b, color=self.numbers_color),
                ).arrange(RIGHT, buff=0.5)
                for b in base_values
            ]
        ).arrange(DOWN, buff=0.5).next_to(sub_title, DOWN, buff=0.7)
        for base in bases:
            base.align_to(bases[0], RIGHT)
            base[0][1].set_color(self.bases_color)

        self.play(Write(sub_title))
        self.play(Write(bases))

        # ---- counting up to 11 ------------------------------------
        steps = 11
        for i in range(steps):
            self.next_slide()
            self.play(*[b[1].animate.set_value(i + 1) for b in bases])

        # ---- count up to 143 quickly ------------------------------
        self.play(*[Count(b[1], steps, 143, LEFT, run_time=6) for b in bases])

        # ---- base-conversion calculator ---------------------------
        bases_calc = VGroup(
            *[
                get_base_convert_calc(b[1], self.numbers_color, self.bases_color)
                .match_height(bases[0][1])
                .match_y(b[1])
                for b in bases
            ]
        )
        bases_calc[0].scale_to_fit_width(config.frame_width * 0.55)
        for calc in bases_calc:
            calc.match_height(bases_calc[0])
        bases_calc.to_edge(RIGHT)

        self.play(bases.animate.to_edge(LEFT))
        calc_arrow = Arrow(
            bases.get_right() + LEFT, bases_calc.get_left() + RIGHT, buff=0.5,
        ).next_to(bases[3], RIGHT)
        sum_eq = MathTex(r"\underset{i=0}{\overset{n}{\sum}}a_{i}b^{i}").next_to(calc_arrow, UP, buff=0)
        color_tex(sum_eq, {"a_{i}": self.numbers_color, "b^{i}": self.bases_color}, tex_class=MathTex)
        self.play(FadeIn(calc_arrow, shift=RIGHT), Write(sum_eq))

        # ---- show calculation: base 2 + base 16 -------------------
        self.next_slide()
        self._animate_base_calc(0, bases, bases_calc)
        self.next_slide()
        self._animate_base_calc(-1, bases, bases_calc)

        self.next_slide()
        self.play(Write(bases_calc[1:-1]))

        # ---- exit bases section -----------------------------------
        self.next_slide()
        self.play(
            Unwrite(sub_title), Unwrite(bases), Unwrite(bases_calc),
            Unwrite(calc_arrow), Unwrite(sum_eq),
        )

    def _animate_base_calc(self, base_idx: int, bases: VGroup, bases_calc: VGroup) -> None:
        int_base = bases[base_idx][1]
        bases_calc[base_idx][::4].set_opacity(0)
        zeroes = int_base.zeroes_padding - len(int_base._get_num_string(int_base.get_value()).lstrip("0"))
        base_cp = bases[base_idx][1].copy()[zeroes:]
        self.play(
            base_cp.animate.move_to(bases_calc[base_idx]).match_height(bases_calc[base_idx][0]),
        )
        self.play(
            *[base_cp[i].animate.move_to(bases_calc[base_idx][i * 4]) for i in range(len(base_cp))],
        )
        self.play(Write(bases_calc[base_idx]))
        bases_calc[base_idx].add(base_cp)

    # -------------------------------------------------------------- example
    def _explain_example(self) -> None:
        example = Tex(
            r"""\begin{itemize}
        \setlength\itemsep{0.03em}
        \item[$\bullet$] $p=$prime number
        \item[$\bullet$] $k\in\mathbb{N}$
        \item[$\bullet$] $U=\left\{ 0,1,\ldots, p^{k}-1\right\}$
        \item[$\bullet$] $x_{i}$ denotes the $i$-th digit of $x$ in base $p$.
        \end{itemize}
        The hash function $h_{a}:U\rightarrow\left\{ 0,1,\ldots p-1\right\}$, where $a\in U$, is defined as follows:
        \[
        h_{a}(x)=\sum_{i=1}^{k}a_{i}x_{i}\ \left(\bmod\ p\right)
        \]""",
            tex_environment=DEFINITION_TEX_ENV,
        ).next_to(self.title, DOWN)
        color_tex(
            example,
            {
                "x": SELECT_KEY_COLOR,
                "x_{i}": SELECT_KEY_COLOR,
                "h_{a}": FUNCS_COLOR,
                "a": FUNCS_COLOR,
                "a_{i}": FUNCS_COLOR,
                "p": self.bases_color,
                "k": self.k_color,
            },
            tex_class=MathTex,
        )
        example[0][31].set_color(self.k_color)
        example[0][134].set_color(self.k_color)
        hash_func_def_idx = 128
        self.hash_func_def = example[0][hash_func_def_idx:]
        self.hash_func_def.to_edge(DOWN)

        last_U_def_idx = 35
        self.play(Write(example[0][1:last_U_def_idx]), Write(example[0][0]))
        self._play_U_example(example, last_U_def_idx)
        self.play(Write(example[0][last_U_def_idx:]))

        self._play_hash_func_example(example, hash_func_def_idx)

    def _play_U_example(self, example_tex, last_U_def_idx: int) -> None:
        self.next_slide()
        p, k = 2, 5
        params = Tex(f"Example: $p={p}$, $k={k}$").next_to(
            example_tex[0][:last_U_def_idx], DOWN, buff=0.7,
        ).to_edge(LEFT)
        color_tex(params, {"p": self.bases_color, "k": self.k_color}, tex_class=MathTex)

        self.region.update(top=params)
        U_eq = Tex("U=").move_to(self.region.center).align_to(params, LEFT)
        U_base10 = self._U_space(p, k, base=10, arrange_cols=(4, 8)).next_to(U_eq, RIGHT)
        U_basep = self._U_space(p, k, arrange_cols=(4, 8)).move_to(U_base10)
        self.play(Write(params))
        self.play(Write(U_base10), Write(U_eq))

        self.next_slide()
        self.play(ReplacementTransform(U_base10, U_basep))

        # ---- second example: p=5, k=3 ------------------------------
        self.next_slide()
        self.play(Unwrite(U_basep))
        p, k = 5, 3
        params2 = Tex(f"Example: $p={p}$, $k={k}$").move_to(params).align_to(params, LEFT)
        color_tex(params2, {"p": self.bases_color, "k": self.k_color}, tex_class=MathTex)
        U_base10 = self._U_space(p, k, base=10).next_to(U_eq, RIGHT)
        U_basep = self._U_space(p, k).move_to(U_base10)
        self.play(TransformMatchingTex(params, params2))
        self.play(Write(U_base10))

        self.next_slide()
        self.play(ReplacementTransform(U_base10, U_basep))

        self.next_slide()
        self.play(Unwrite(params2), Unwrite(U_eq), Unwrite(U_basep))

    def _U_space(self, p: int, k: int, *, base: int | None = None, arrange_cols=None) -> VGroup:
        base = p if base is None else base
        arrange_cols = (p, p ** (k - 1)) if arrange_cols is None else arrange_cols
        return (
            VGroup(
                *[
                    IntegerBase(i, base, zeroes_padding=k, zeroes_opacity=1, color=WHITE)
                    for i in range(p**k)
                ]
            )
            .arrange_in_grid(*arrange_cols, flow_order="dr")
            .scale_to_fit_width(config.frame_width * 0.86)
            .set_color(SELECT_KEY_COLOR)
        )

    def _play_hash_func_example(self, example_tex, hash_func_def_idx: int) -> None:
        self.next_slide()
        self.play(Unwrite(example_tex[0][:hash_func_def_idx]))

        p, k, a = 5, 2, 8
        keys_size = 10
        fmt = IntegerBase(0, p, zeroes_padding=k)._get_num_string
        funcs_bowl = get_funcs_bowl(fmt, f"{p - 1}" * k, [5, 5])
        ht = HashTable(
            keys_size,
            p,
            lambda x: get_hash_func(p, k, a)(x if x != keys_size - 1 else p**k - 1),
            arrows_config={
                "tip_length": 1.5,
                "stroke_width": 6,
                "max_tip_length_to_length_ratio": 0.35,
            },
            keys_array_gap_size=7,
        )

        # Halve the index buff distance, set indices + clear values, then shift back.
        # simplex.mobjects.ArrayEntry uses a module-local _INDEX_BUFF so we tweak
        # placement manually instead of mutating it.
        for i, entry in enumerate(ht.array):
            entry.set_index(i)
            entry.set_value("")
            # match dastimator's halved INDICES_BUFF look: nudge the index closer to the frame.
            entry.index_mob.shift(UP * entry.index_mob.height * 0.5)
        for i, key in enumerate(ht.keys):
            if i == ht.keys_size - 2:
                continue
            key.set_value(f"{p - 1}" * k if i == ht.keys_size - 1 else fmt(i))

        ht.to_edge(DR)
        funcs_bowl.scale(0.7).next_to(ht, LEFT, buff=1).align_to(ht.keys, UP).shift(DOWN * 0.2)
        select_arrow = CurvedArrow(
            funcs_bowl.get_top() * RIGHT + ht.get_top() * UP,
            ht.get_top(),
            angle=-TAU / 6,
            color=GREEN,
            stroke_width=6,
        )
        select_text = MathTex(r"h", f"_{{{fmt(a)}}}", color=YELLOW).next_to(select_arrow, UP, buff=0.1)
        select_arrow.add(select_text)

        params = Tex(f"Example: $p={p}$, $k={k}$").next_to(funcs_bowl, DOWN).align_to(self.title, LEFT)
        color_tex(params, {"p": self.bases_color, "k": self.k_color}, tex_class=MathTex)

        self.play(self.hash_func_def.animate.next_to(self.title, DOWN, buff=0.2).align_to(self.title, LEFT))
        self.play(Write(params), Write(ht), Write(funcs_bowl))
        self.play(Write(select_arrow))

        # ---- first calc ---------------------------------------------
        self.next_slide()
        x_1 = 3
        eq, mod = get_hash_func_calc(p, k, a, x_1, self.bases_color, SELECT_KEY_COLOR, FUNCS_COLOR)
        self.region.update(top=params, right=ht)
        VGroup(eq, mod).move_to(self.region.center)
        self.play(
            Write(eq[:-1]),
            Write(mod),
            ht.keys[x_1].value_mob.animate.set_color(SELECT_KEY_COLOR),
        )
        self.next_slide()
        self.play(Write(eq[-1]))

        # ---- second calc --------------------------------------------
        self.next_slide()
        x_2 = 7
        eq2, _ = get_hash_func_calc(p, k, a, x_2, self.bases_color, SELECT_KEY_COLOR, FUNCS_COLOR)
        eq2.move_to(eq).align_to(eq, LEFT)
        self.play(Unwrite(eq[-1]), ht.keys[x_1].value_mob.animate.set_color(WHITE))
        self.play(
            ReplacementTransform(eq[:-1], eq2[:-1]),
            ht.keys[x_2].value_mob.animate.set_color(SELECT_KEY_COLOR),
        )
        self.next_slide()
        self.play(Write(eq2[-1]))

        self.next_slide()
        self.play(
            Unwrite(params), Unwrite(ht), Unwrite(funcs_bowl), Unwrite(select_arrow),
            Unwrite(eq2), Unwrite(mod),
        )

    # ---------------------------------------------------------------- proof
    def _proof_of_universal_hash_family(self) -> None:
        self.next_slide(name="Universal Hash Families Example 3 - Proof")
        question = Tex(
            r"Is $\mathcal{H}=\left\{ h_{a}\middle|a\in U\right\}$ a universal hash family?"
        ).next_to(self.title, DOWN).align_to(self.title, LEFT)
        color_tex(question, {"h_{a}": FUNCS_COLOR}, tex_class=MathTex)
        reminder = get_univ_def_reminder().scale(0.7).to_edge(DL, buff=0.3)
        self.play(self.hash_func_def.animate.next_to(reminder, UP))
        self.play(Write(question))
        self.play(Write(reminder))

        # ---- proof equations ---------------------------------------
        self.next_slide()
        proof = VGroup(
            MathTex(
                r"P\left[h_{a}(x)=h_{a}(y)\right]",
                r"=&P\left[\sum_{i=1}^{k}a_{i}\cdot x_{i}=\sum_{i=1}^{k}a_{i}\cdot y_{i}"
                r"\ \left(\bmod\ p\right)\right]",
            ),
            MathTex(
                r"=P\left[\sum_{i=1}^{k}a_{i}\cdot\left(x_{i}-y_{i}\right)=0"
                r"\ \left(\bmod\ p\right)\right]"
            ),
            MathTex(
                r"=P\left[\sum_{i\neq j}a_{i}\cdot\left(x_{i}-y_{i}\right)"
                r"+a_{j}\left(x_{j}-y_{j}\right)=0\ \left(\bmod\ p\right)\right]"
            ),
            MathTex(
                r"=P\left[\sum_{i\neq j}a_{i}\cdot\left(x_{i}-y_{i}\right)"
                r"=a_{j}\left(y_{j}-x_{j}\right)\ \left(\bmod\ p\right)\right]"
            ),
            MathTex(
                r"=P\left[\frac{\sum_{i\neq j}a_{i}\cdot\left(x_{i}-y_{i}\right)}"
                r"{\left(y_{j}-x_{j}\right)}=a_{j}\ \left(\bmod\ p\right)\right]",
                r"=\frac{1}{p}",
            ),
        ).arrange(DOWN, buff=0.3).scale_to_fit_height(
            (config.frame_height - question.get_bottom()[1]) * 0.95,
        )
        for i, line in enumerate(proof):
            color_tex(
                line,
                {
                    "x": SELECT_KEY_COLOR, "y": SELECT_KEY_COLOR,
                    "x_{i}": SELECT_KEY_COLOR, "y_{i}": SELECT_KEY_COLOR,
                    "x_{j}": SELECT_KEY_COLOR, "y_{j}": SELECT_KEY_COLOR,
                    "a_{i}": FUNCS_COLOR, "a_{j}": FUNCS_COLOR, "h_{a}": FUNCS_COLOR,
                    "p": self.bases_color,
                },
                tex_class=MathTex,
            )
            if i != 0:
                line.align_to(proof[0][1], LEFT)

        proof.next_to(question, DOWN, buff=0.25).align_to(self.title, RIGHT)

        self.region.update(left=self.hash_func_def, top=proof[0][0], bottom=proof[-1][-1])
        vdots = MathTex(r"\vdots").scale(3).move_to(self.region.center)
        self.play(Write(proof[0][0]), Write(vdots), Write(proof[-1][-1]))

        # ---- step-through ------------------------------------------
        steps = VGroup(proof[0][1], *proof[1:-1], proof[-1][0])
        self.next_slide()
        self.play(Unwrite(vdots))
        self.play(Write(steps[0]))

        for i, step in enumerate(steps[1:], start=1):
            self.next_slide()
            prev = steps[i - 1].copy()
            self.play(prev.animate.match_y(step))
            self.play(TransformMatchingShapes(prev, step))

        # ---- exit --------------------------------------------------
        self.next_slide()
        self.play(
            Unwrite(proof), Unwrite(question), Unwrite(reminder),
            Unwrite(self.hash_func_def), Unwrite(self.title),
        )
