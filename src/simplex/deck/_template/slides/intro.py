"""Template scenes -- a title slide plus a second content slide."""

from manim import DOWN, ORIGIN, VGroup, Tex, Write, FadeIn

from simplex import Slide, get_active_theme


class Intro(Slide):
    title: str = "Hello, Simplex"
    subtitle: str = r"$f(x) = e^{i\pi} + 1 = 0$"

    def construct(self) -> None:
        theme = get_active_theme()
        title_mob = Tex(self.title, font_size=theme.typography.h1)
        self.region.place(title_mob, ORIGIN)

        sub = Tex(self.subtitle, font_size=theme.typography.h2)
        sub.next_to(title_mob, DOWN, buff=0.4)
        self.play(Write(title_mob), Write(sub))
        self.next_slide()


class KeyIdea(Slide):
    title: str = "A Second Slide"
    body: str = "Use notes for citations, slide refs, and supporting detail."

    def construct(self) -> None:
        theme = get_active_theme()
        title_mob = Tex(self.title, font_size=theme.typography.h2, color=theme.palette.accent)
        body_mob = Tex(self.body, font_size=theme.typography.body)
        group = VGroup(title_mob, body_mob).arrange(DOWN, buff=0.45)
        self.region.place(group, ORIGIN)

        self.play(Write(title_mob), FadeIn(body_mob, shift=DOWN * 0.2))
        self.next_slide()
