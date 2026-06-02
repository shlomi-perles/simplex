"""Showcase: Paper mobject -- PDF stack, pick animation, and dismiss.

Demonstrates ``simplex.mobjects.Paper`` with the "Attention Is All You Need"
paper from ArXiv. Shows the full lifecycle: intro -> pick -> dismiss.
"""

from manim import DL, DOWN, RIGHT, UP, Tex, Write

from simplex.mobjects.paper import DismissPaper, Paper, PickPage, ShowPaper
from simplex.slides import Slide

try:
    from slides.showcase_style import setup_showcase_chrome
except ModuleNotFoundError:  # direct ``manim slides/paper_showcase.py ...`` execution
    from showcase_style import setup_showcase_chrome


class PaperShowcase(Slide):
    """Paper Mobject -- ArXiv PDF stacking, picking, and dismissal."""

    def setup(self) -> None:
        super().setup()
        setup_showcase_chrome(
            self,
            r"mobjects/paper.py -- Paper + ShowPaper + PickPage + DismissPaper",
        )

    def construct(self) -> None:
        title = Tex(r"\textbf{Attention Is All You Need} \\ Vaswani et al., 2017")
        title.scale(0.8)
        self.region.place(title, UP, buff=0.2)
        self.play(Write(self.showcase_title), Write(title))

        # Directions are vanilla Manim vectors (DL, RIGHT, DOWN, ...).
        paper = Paper(
            "https://arxiv.org/abs/1706.03762",
            pages=3,
            dpi=150,
            page_height=4.5,
            shadow=True,
            shadow_direction=DL,
            stack_direction=DL,
        )
        self.region.place(paper, buff=0.3)

        self.play(ShowPaper(paper, direction=DOWN))
        self.next_slide()

        self.play(PickPage(paper, page_index=2, slide_direction=RIGHT, overshoot=4.0))
        self.next_slide()

        self.play(PickPage(paper, page_index=1, slide_direction=RIGHT, overshoot=4.0))
        self.next_slide()

        self.play(DismissPaper(paper, direction=DOWN))
        self.next_slide()
        self.clear_scene()
