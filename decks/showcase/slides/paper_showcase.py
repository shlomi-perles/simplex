"""Showcase: Paper mobject -- PDF stack, pick animation, and dismiss.

Demonstrates ``simplex.mobjects.Paper`` with the "Attention Is All You Need"
paper from ArXiv. Shows the full lifecycle: intro -> pick -> dismiss.
"""

from manim import UP, Tex, Write

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
        paper_title = Tex(r"\textbf{Attention Is All You Need} \\ Vaswani et al., 2017")
        self.region.place(paper_title, UP)
        self.region.update(top=paper_title)
        self.play(Write(self.canvas["showcase_title"]), Write(paper_title))

        # Directions are vanilla Manim vectors (DL, RIGHT, DOWN, ...).
        paper = Paper("https://arxiv.org/abs/1706.03762")
        self.region.scale_and_place(paper)

        self.play(ShowPaper(paper))
        self.next_slide()

        self.play(PickPage(paper, page_index=2))
        self.next_slide()

        self.play(PickPage(paper, page_index=1))
        self.next_slide()

        self.play(DismissPaper(paper))
        self.next_slide()
        self.clear_scene()
