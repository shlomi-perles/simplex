"""Template intro scene -- one slide with a title + subtitle."""

from manim import DOWN, Tex, Write

from simplex.slides import BaseSlide
from simplex.theme.context import get_active_theme


class Intro(BaseSlide):
    title: str = "Hello, Simplex"
    subtitle: str = r"$f(x) = e^{i\pi} + 1 = 0$"

    def construct(self) -> None:
        theme = get_active_theme()
        title_mob = Tex(self.title, font_size=theme.typography.h1)
        self.region.place(title_mob, "center")

        sub = Tex(self.subtitle, font_size=theme.typography.h2)
        sub.next_to(title_mob, DOWN, buff=0.4)
        self.play(Write(title_mob), Write(sub))
        self.next_slide()
