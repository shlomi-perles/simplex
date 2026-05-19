"""Title + agenda slide for the adaptive preconditioning lecture."""

from manim import DOWN, RIGHT, UP, FadeIn, Tex, VGroup, Write

from simplex.engine.text import Caption
from simplex.slides import BaseSlide
from simplex.theme.context import get_active_theme

from common import C_ADAM, C_GD, C_MOMENTUM, C_VARIANCE
from equation_lab import kicker_equation


class Intro(BaseSlide):
    """Opening: title + 1-line subtitle + colored agenda chips."""

    title: str = r"Adaptive Learning Rates"
    subtitle: str = r"From Momentum GD to AdaGrad and ADAM"

    def construct(self) -> None:
        theme = get_active_theme()
        title_mob = Tex(self.title, font_size=theme.typography.h1)
        self.region.place(title_mob, "center")
        title_mob.shift(UP * 0.6)

        sub = Tex(self.subtitle, font_size=theme.typography.h2, color=C_GD)
        sub.next_to(title_mob, DOWN, buff=0.4)

        formula_preview = kicker_equation(font_size=46)
        formula_preview.next_to(sub, DOWN, buff=0.9)

        agenda = self._agenda_chips()
        agenda.next_to(formula_preview, DOWN, buff=0.9)

        self.play(Write(title_mob))
        self.play(Write(sub))
        self.next_slide()

        self.play(Write(formula_preview))
        self.next_slide()

        self.play(FadeIn(agenda, shift=UP * 0.3))
        self.next_slide()

    def _agenda_chips(self) -> VGroup:
        items = (
            ("1.\\ Momentum", C_MOMENTUM),
            ("2.\\ AdaGrad", C_VARIANCE),
            ("3.\\ ADAM", C_ADAM),
        )
        chips = VGroup(
            *(Caption(text, color=color) for text, color in items),
        )
        chips.arrange(RIGHT, buff=1.4)
        return chips
