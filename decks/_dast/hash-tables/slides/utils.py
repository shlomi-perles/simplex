"""Hash-tables-specific helpers: small mobjects + constants + factories.

Everything generic (color_tex, the Region API, ArrayMob, ArrayPointer) is
imported from simplex. This module only holds what's bespoke to the deck:
universal-hash-family definitions, the IntegerBase decimal-number variant,
the bowl-of-hash-functions visual, and the random hash-family table.
"""

from __future__ import annotations

import string

import numpy as np
from manim import (
    BLUE,
    DOWN,
    GREEN,
    LEFT,
    PI,
    RIGHT,
    UP,
    YELLOW,
    Animation,
    Arc,
    Arrow,
    BackgroundRectangle,
    DecimalNumber,
    DARK_GREY,
    Integer,
    MathTex,
    MobjectTable,
    Square,
    SurroundingRectangle,
    Tex,
    Text,
    Union,
    VGroup,
    WHITE,
    config,
)

from simplex.engine.text import color_tex

from hash_table import HashTable


# ----------------------------- semantic colors ----------------------------
FUNCS_COLOR = YELLOW
SELECT_KEY_COLOR = BLUE
K_UNIVERSAL_COLOR = GREEN
PROB_BG_CELL_COLOR = "#4f6c44"
PROBABILITY_SPACE_BACK_COLOR = "#404040"

SUB_TITLES_SCALE = 0.7
HASH_TABLE_FUNCS_TITLE_BUFF = -0.15
DEFAULT_HASH_FAMILY_TABLE_SIZE = 4

# Compact 8cm minipage matches dastimator's DEFINITION_TEX_ENV.
DEFINITION_TEX_ENV = "{minipage}{8cm}"


# ------------------------------ definitions -------------------------------

def get_universal_hash_family_def() -> MathTex:
    eq = MathTex(
        r"\forall x\neq y\in U,"
        r"\underset{h\in\mathcal{H}}{\mathbb{P}}"
        r"\left[h\left(x\right)=h\left(y\right)\right]\leq\frac{1}{m}",
    )
    color_tex(eq, {"x": SELECT_KEY_COLOR, "y": SELECT_KEY_COLOR, "h": FUNCS_COLOR}, tex_class=MathTex)
    return eq


def get_two_universal_def() -> MathTex:
    eq = MathTex(
        r"\begin{matrix}\begin{matrix}\mathbin{\forall}y_{1}\neq y_{2}\in U\\"
        r"\mathbin{\forall}i_{1},i_{2}\in\left[m\right]"
        r"\end{matrix}\\"
        r"\underset{h\in\mathcal{H}}{\mathbb{P}}\left[h\left(y_{1}\right)=i_{1}"
        r"\land h\left(y_{2}\right)=i_{2}\right]\leq\frac{1}{m^{2}}"
        r"\end{matrix}",
    )
    color_tex(
        eq,
        {"y_{1}": SELECT_KEY_COLOR, "y_{2}": SELECT_KEY_COLOR, "h": FUNCS_COLOR},
        tex_class=MathTex,
    )
    eq[0][-1].set_color(K_UNIVERSAL_COLOR)
    return eq


def get_univ_def_reminder() -> VGroup:
    title = Text("Reminder (Universal Hash Family):").scale(0.7)
    eq = get_universal_hash_family_def().next_to(title, DOWN).align_to(title, LEFT)
    text = VGroup(title, eq)
    rect = SurroundingRectangle(
        text,
        stroke_color=WHITE,
        fill_color=DARK_GREY,
        corner_radius=0.1,
        fill_opacity=0.8,
    )
    return VGroup(rect, text)


# --------------------------- bowl of hash functions -----------------------

def get_funcs_bowl(num_format=int, last_func_idx: str = r"\left|\mathcal{H}\right|", gaps=None) -> VGroup:
    gaps = gaps if gaps is not None else [7, 5]
    bowl = Arc(start_angle=PI, angle=PI).scale(3)

    row1 = VGroup(*[MathTex(rf"h_{{{num_format(i)}}}").scale(1.3) for i in range(1, 1 + gaps[0])])
    row1.arrange(RIGHT)
    row2 = VGroup(
        *[MathTex(rf"h_{{{num_format(i)}}}").scale(1.3) for i in range(1 + gaps[0], 1 + gaps[0] + gaps[1])]
    )
    row2.arrange(RIGHT).next_to(row1, DOWN)

    funcs = VGroup(row1, row2)
    funcs += MathTex(r"\vdots").next_to(funcs, DOWN)
    funcs += MathTex(rf"h_{{{last_func_idx}}}").next_to(funcs, DOWN).scale(1.3)

    funcs.match_height(bowl).scale(0.9).move_to(bowl).set_color(FUNCS_COLOR)
    return VGroup(bowl, funcs)


# --------------------------- main hash table example ----------------------

def get_main_hash_table_example(title) -> tuple[np.ndarray, HashTable]:
    """Centered hash table + frame center of the body region below ``title``."""
    from simplex.engine.region import Region

    body = Region.full_frame()
    body.update(top=title)
    frame_center = body.center

    hash_map = {0: 1, 1: 0, 2: 2, 3: 3, 5: 2}
    ht = HashTable(
        6,
        5,
        lambda i: hash_map[i],
        keys_array_gap_size=6,
        arrows_config={
            "tip_length": 1.5,
            "stroke_width": 6,
            "max_tip_length_to_length_ratio": 0.35,
        },
    ).scale_to_fit_height(config.frame_height * 0.5)
    ht.shift(-ht.keys.get_center()).set_y(frame_center[1]).shift(DOWN * 0.6)
    return frame_center, ht


def get_hash_table_subtitles(ht: HashTable) -> tuple[Text, Text, MathTex]:
    array_text = Text("array").scale(SUB_TITLES_SCALE).next_to(ht, UP, buff=1.2).match_x(ht.array)
    keys_text = Text("keys").scale(SUB_TITLES_SCALE).next_to(ht, UP, buff=1.2).match_x(ht.keys)
    h_text = (
        MathTex(r"h", color=FUNCS_COLOR)
        .next_to(ht, UP, buff=HASH_TABLE_FUNCS_TITLE_BUFF)
        .match_x(ht)
    )
    return array_text, keys_text, h_text


# ------------------------- hash family probability table -------------------

def get_hash_family_table(array_size: int, keys_size: int, *, table_size: int = DEFAULT_HASH_FAMILY_TABLE_SIZE, seed=None) -> MobjectTable:
    if seed is not None:
        np.random.seed(seed)
    mapping = [
        [{i: np.random.randint(0, array_size) for i in range(keys_size)} for _ in range(table_size)]
        for _ in range(table_size)
    ]
    tables = [
        [
            HashTable(
                keys_size,
                array_size,
                lambda x, i=i, j=j: mapping[i][j][x],
                arrows_config={"tip_length": 2, "stroke_width": 3},
                keys_array_gap_size=3.5,
            )
            for i in range(table_size)
        ]
        for j in range(table_size)
    ]
    tables[-2][-1] = MathTex(r"\vdots").scale(4.5)
    tables[-1][-2] = MathTex(r"\ldots").scale(4.5)
    tab = (
        MobjectTable(tables, include_outer_lines=True)
        .scale_to_fit_height(config.frame_height * 0.8)
        .to_edge(LEFT)
    )
    tab += BackgroundRectangle(tab, color=PROBABILITY_SPACE_BACK_COLOR, z_index=-30)
    return tab


def animate_collision_prob(
    i: int,
    j: int,
    hashs_tab: MobjectTable,
    bg_cells: VGroup | None = None,
    i_1: int | None = None,
    i_2: int | None = None,
    *,
    cell_color: str = PROB_BG_CELL_COLOR,
    cells_opacity: float = 1.0,
    change_others_opacity: bool = True,
) -> list[Animation]:
    """Animate which hash tables in ``hashs_tab`` collide on ``(i, j)``.

    If ``i_1`` and ``i_2`` are given, instead match the (i_1, i_2) outcome.
    """
    animations: list[Animation] = []
    if bg_cells is None:
        bg_cells = VGroup(
            *[
                VGroup(
                    *[
                        hashs_tab.get_highlighted_cell((j_t, i_t), color=cell_color, fill_opacity=0, z_index=-20)
                        for i_t in range(1, hashs_tab.row_dim + 1)
                    ]
                )
                for j_t in range(1, hashs_tab.col_dim + 1)
            ]
        )

    for cell in hashs_tab.elements:
        if not isinstance(cell, HashTable):
            continue
        for key_idx, key in enumerate(cell.keys):
            animations.append(
                key.value_mob.animate.set_color(
                    SELECT_KEY_COLOR if key_idx in (i, j) else WHITE,
                ),
            )

    for i_tab in range(1, hashs_tab.row_dim + 1):
        for j_tab in range(1, hashs_tab.col_dim + 1):
            colored: list[Arrow] = []
            ht = hashs_tab.get_entries((i_tab, j_tab))
            if not isinstance(ht, HashTable):
                continue
            collide_simple = ht.hash_func(i) == ht.hash_func(j) and (i_1 is None or i_2 is None)
            collide_specific = ht.hash_func(i) == i_1 and ht.hash_func(j) == i_2
            if collide_simple or collide_specific:
                animations.append(
                    bg_cells[i_tab - 1][j_tab - 1].animate.set_fill(color=cell_color, opacity=cells_opacity),
                )
                for idx in (i, j):
                    colored.append(ht.get_arrow(idx))
                    animations.append(ht.get_arrow(idx).animate.set_color(SELECT_KEY_COLOR).set_z_index(10))
                    animations.append(ht.keys[idx].value_mob.animate.set_color(SELECT_KEY_COLOR))
            elif change_others_opacity:
                animations.append(bg_cells[i_tab - 1][j_tab - 1].animate.set_fill(opacity=0))
            else:
                continue

            for arrow in ht.arrows:
                if arrow not in colored:
                    animations.append(arrow.animate.set_color(FUNCS_COLOR).set_z_index(1))
    return animations


# ----------------------------- base-changing -------------------------------

def get_hash_func(p: int, k: int, a: int):
    return lambda x: int(sum((a // p**i % p) * (x // p**i % p) for i in range(k))) % p


class IntegerBase(Integer):
    """An ``Integer`` mobject that renders in an arbitrary base with leading-zero padding."""

    def __init__(self, value, base, *, zeroes_padding: int = 8, zeroes_opacity: float = 0.3, **kwargs):
        self.base = base
        self.zeroes_padding = zeroes_padding
        self.zeroes_opacity = zeroes_opacity
        self.digs = string.digits + string.ascii_uppercase
        super().__init__(value, **kwargs)
        self.set_value(value)

    def set_value(self, value, *, align_digits: bool = True):
        old = self.copy()
        super().set_value(value)
        zeroes = self.zeroes_padding - len(self._get_num_string(value).lstrip("0"))
        if zeroes > 0:
            self[:zeroes].set_opacity(self.zeroes_opacity)
        if align_digits:
            for i, digit in enumerate(self):
                digit.match_x(old[i])

    def _get_num_string(self, number):
        number = int(np.round(number, self.num_decimal_places))
        if number == 0:
            return self.digs[0].zfill(self.zeroes_padding)
        sign = -1 if number < 0 else 1
        number *= sign
        digits: list[str] = []
        while number:
            digits.append(self.digs[number % self.base])
            number //= self.base
        if sign < 0:
            digits.append("-")
        digits.reverse()
        return "".join(digits).zfill(self.zeroes_padding)


class Count(Animation):
    """Linearly interpolate the displayed value of a ``DecimalNumber``."""

    def __init__(self, number: DecimalNumber, start: float, end: float, align=None, **kwargs) -> None:
        super().__init__(number, **kwargs)
        self.start = start
        self.end = end
        self.origin_mob = number.copy()
        self.align = align

    def interpolate_mobject(self, alpha: float) -> None:
        self.mobject.set_value(self.start + alpha * (self.end - self.start))
        if self.align is not None:
            self.mobject.align_to(self.origin_mob, self.align)


def get_base_convert_calc(number: IntegerBase, number_color: str, base_color: str, *, no_padding: bool = True) -> MathTex:
    s = number._get_num_string(number.get_value())
    if no_padding:
        s = s.lstrip("0")
    parts: list[str] = []
    for idx, dig in enumerate(s):
        dig_val = number.digs.index(dig)
        parts.append(f"{dig_val}")
        parts.append(r"\cdot")
        parts.append(rf"{number.base}^{{{len(s) - idx - 1}}}")
        if idx != len(s) - 1:
            parts.append(r"+")
    out = MathTex(*parts)
    out[0::4].set_color(number_color)
    out[2::4].set_color(base_color)
    return out


def get_hash_func_calc(p: int, k: int, a: int, x: int, base_color, keys_color, hash_color) -> tuple[MathTex, MathTex]:
    fmt = IntegerBase(x, p, zeroes_padding=k)._get_num_string
    a_str, x_str = fmt(a), fmt(x)
    parts = [rf"h_{{{a_str}}}\left({x_str}\right)="]
    for i in range(k):
        parts.append(rf"{a_str[i]}")
        parts.append(r"\cdot")
        parts.append(rf"{x_str[i]}")
        if i != k - 1:
            parts.append(r"+")
    parts.append(rf" = {get_hash_func(p, k, a)(x)}")
    eq = MathTex(*parts)
    eq[1:-1:4].set_color(hash_color)
    eq[3:-1:4].set_color(keys_color)
    color_tex(eq, {f"h_{{{a_str}}}": hash_color, f"{x_str}": keys_color}, tex_class=MathTex)
    mod = MathTex(rf"\ \left(\bmod\ {p}\right)").next_to(eq, RIGHT)
    mod[0][-2].set_color(base_color)
    return eq, mod


# ----------------------------- union bound icon ----------------------------

def get_unit_bound() -> VGroup:
    bg = Square(fill_color=PROBABILITY_SPACE_BACK_COLOR, fill_opacity=1).set_z_index(-10)
    right = VGroup(bg.copy(), MathTex(r"+").scale(1.5), bg.copy()).set_z_index(-10)
    leq = MathTex(r"\leq").scale(1.5)
    e1 = Square(stroke_color=GREEN, fill_color=PROB_BG_CELL_COLOR, fill_opacity=1).scale(0.6).align_to(bg, LEFT + UP)
    e2 = e1.copy().align_to(bg, RIGHT + DOWN)
    bg.add(Union(e1, e2, color=PROB_BG_CELL_COLOR, fill_opacity=1).set_stroke(GREEN))
    right[0].add(e1)
    right[2].add(e2)
    right.arrange(RIGHT, buff=0.2)
    return VGroup(bg, leq, right).arrange(RIGHT, buff=0.3)


# ------------------------ Function-call text helper -----------------------

def get_func_text(string: str, blue_args: list | None = None, **kwargs):
    """A monospace string with name in yellow, integer/listed args in blue."""
    import re

    blue_args = blue_args or []
    func_name = string.split("(")[0]
    numbers = [int(n) for n in re.findall(r"\d+", string)]
    return Text(
        string,
        font="JetBrains Mono",
        t2c={
            func_name: YELLOW,
            ",": "#FFA500",  # ORANGE
            **{str(n): BLUE for n in numbers},
            **{arg: BLUE for arg in blue_args},
        },
        **kwargs,
    )


# ----------------------- code-tex inline math helper -----------------------

CODE_MATH_SCALE = 0.9


def compile_code_tex_line(line_mob, line_str: str, line_start_idx: int = 0, *, bold_math: bool = True):
    """Replace ``$...$`` substrings in a rendered Text with Tex math glyphs."""
    import re

    matches = re.findall(r"\$(.*?)\$", line_str)
    spans = [("$" + m + "$", line_str.index("$" + m + "$")) for m in matches]
    for s, idx in spans:
        idx += line_start_idx
        replace_word = line_mob[idx:idx + len(s)]
        body = s.strip("$")
        tex_src = rf"$\boldsymbol{{{body}}}$" if bold_math else f"${body}$"
        tex = (
            Tex(tex_src)
            .match_height(replace_word[1:-1])
            .scale(CODE_MATH_SCALE)
            .move_to(replace_word, aligned_edge=LEFT)
            .set_stroke(width=0, opacity=0)
        )
        replace_word[-1].become(tex)
        replace_word[:-1].become(VGroup().scale(0).move_to(tex.get_right()))
        replace_word.set_stroke(width=0, opacity=0)
        line_mob[idx + len(s):].next_to(replace_word[-1], buff=0.05)
