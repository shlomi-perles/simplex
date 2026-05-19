"""Universal Hash Examples 1 & 2 -- two tiny families."""

from __future__ import annotations

from manim import (
    DOWN,
    LEFT,
    RIGHT,
    UP,
    MathTex,
    Tex,
    Title,
    TransformMatchingShapes,
    Unwrite,
    VGroup,
    Write,
    config,
)

from simplex.engine.text import color_tex
from simplex.slides import BaseSlide

from hash_table import HashTable
from utils import (
    FUNCS_COLOR,
    HASH_TABLE_FUNCS_TITLE_BUFF,
    SELECT_KEY_COLOR,
    get_univ_def_reminder,
)


def _small_hash_table() -> HashTable:
    ht = HashTable(3, 2, lambda x: 0 if x == 1 else 1)
    ht.keys[1].set_opacity(0)
    ht.keys[-1].next_to(ht.keys[0], DOWN, buff=0)
    ht.keys.match_y(ht.array)
    for key, val in zip([0, 2], [0, 1]):
        ht.keys[key].set_value(val)
    ht.array[0].value_mob.set_opacity(0)
    for idx in range(2):
        ht.array[idx].set_index(idx)
    return ht


class UniversalHashExamples(BaseSlide):
    def construct(self) -> None:
        self.next_slide(name="Universal Hash Families Examples 1+2")
        title = Title("Universal Hash Families - Example ", "1")
        self.play(Write(title))

        family = VGroup(_small_hash_table(), _small_hash_table()).arrange(DOWN, buff=1)
        h1 = MathTex(r"h_1", color=FUNCS_COLOR).next_to(family[0], UP, buff=HASH_TABLE_FUNCS_TITLE_BUFF)
        h2 = MathTex(r"h_2", color=FUNCS_COLOR).next_to(family[1], UP, buff=HASH_TABLE_FUNCS_TITLE_BUFF)
        family += VGroup(h1, h2)
        family[0].rehash(lambda x: 0 if x == 2 else 1)
        family[1].rehash(lambda x: 1 if x == 2 else 0)
        family.scale_to_fit_height(config.frame_height * 0.75).next_to(title, DOWN).to_edge(RIGHT)

        self.region.update(top=title, right=family)
        frame_center = self.region.center
        q = Tex(r"Is $\mathcal{H}$ a universal hash family?").next_to(title, DOWN, buff=0.65).set_x(
            frame_center[0],
        )
        self.play(Write(q))
        self.play(Write(family))

        # ---- reminder ----------------------------------------------
        self.next_slide()
        reminder = get_univ_def_reminder().to_edge(DOWN, buff=0.4).set_x(frame_center[0])
        self.play(Write(reminder), q.animate.align_to(title, LEFT))

        # ---- solution ----------------------------------------------
        self.next_slide()
        self.region.update(top=q, right=family, bottom=reminder)
        sol = MathTex(
            r"\underset{h\in\mathcal{H}}{\mathbb{P}}\left[h\left(0\right)=h\left(1\right)\right]=",
            "0",
            r"\leq\frac{1}{m}=\frac{1}{2}",
        ).move_to(self.region.center)
        color_tex(
            sol[0],
            {"h": FUNCS_COLOR, "0": SELECT_KEY_COLOR, "1": SELECT_KEY_COLOR},
            tex_class=MathTex,
        )
        self.play(Write(sol[0]))
        self.next_slide()
        self.play(Write(sol[1]))
        self.next_slide()
        self.play(Write(sol[2]))

        # ---- example 2 ---------------------------------------------
        self.next_slide()
        title_2 = Title("Universal Hash Families - Example ", "2")
        self.play(TransformMatchingShapes(title[1], title_2[1]), Unwrite(sol))
        self.wait()
        self.play(
            family[0].animate.rehash(lambda x: 0),
            family[1].animate.rehash(lambda x: 1),
        )

        self.next_slide()
        sol = MathTex(
            r"\underset{h\in\mathcal{H}}{\mathbb{P}}\left[h\left(0\right)=h\left(1\right)\right]=",
            "1",
            r">\frac{1}{m}=\frac{1}{2}",
        ).move_to(sol)
        color_tex(
            sol[0],
            {"h": FUNCS_COLOR, "0": SELECT_KEY_COLOR, "1": SELECT_KEY_COLOR},
            tex_class=MathTex,
        )
        self.play(Write(sol[0]))
        self.next_slide()
        self.play(Write(sol[1]))
        self.next_slide()
        self.play(Write(sol[2]))

        # ---- exit ---------------------------------------------------
        self.next_slide()
        self.play(
            *map(Unwrite, (title[:1], title[2:], title_2[1], family, q, reminder, sol)),
        )
        self.wait()
