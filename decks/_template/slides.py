"""Template deck -- a single intro slide."""

from simplex.slides import BaseSlide
from simplex.theme.context import get_active_theme
from manim import DOWN, Tex, Write




class Intro(BaseSlide):
    title = "Hello, Simplex"
    subtitle = r"$f(x) = e^{i\pi} + 1 = 0$"

    def construct(self) -> None:
        theme = get_active_theme()
        title_mob = Tex(self.title, font_size=theme.typography.h1)
        self.region.place(title_mob, "center")
        
        if self.subtitle:
            sub = Tex(self.subtitle, font_size=theme.typography.h2)
            sub.next_to(title_mob, DOWN, buff=0.4)
            self.playt(Write(title_mob), Write(sub))
        else:
            self.playt(Write(title_mob))
            
        self.next_slide()
