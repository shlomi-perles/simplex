"""Showcase: Paper mobject -- PDF stack, pick animation, and dismiss.

Demonstrates ``simplex.mobjects.Paper`` with the "Attention Is All You Need"
paper from ArXiv. Shows the full lifecycle: intro -> pick -> dismiss.
"""

from manim import RIGHT, UP, Tex, Write

from simplex.mobjects.paper import DismissPaper, Paper, PickPage, ShowPaper
from simplex.slides import BaseSlide, make_chrome
from simplex.theme.context import get_active_theme


class PaperShowcase(BaseSlide):
    """Paper Mobject -- ArXiv PDF stacking, picking, and dismissal."""

    def setup(self) -> None:
        super().setup()
        chrome = make_chrome(
            get_active_theme(),
            self.region,
            header=r"mobjects/paper.py -- Paper + ShowPaper + PickPage + DismissPaper",
        )
        self.add_to_canvas(**chrome.mobjects)
        self.region = chrome.body_region

    def construct(self) -> None:
        title = Tex(r"\textbf{Attention Is All You Need} \\ Vaswani et al., 2017")
        title.scale(0.8)
        self.region.place(title, UP, buff=0.2)
        self.play(Write(title))
        self.next_slide(name="PaperShowcase")

        paper = Paper(
            "https://arxiv.org/abs/1706.03762",
            pages=3,
            dpi=150,
            page_height=4.5,
            shadow=True,
            shadow_direction="DL",
            stack_direction="DL",
        )
        self.region.place(paper, buff=0.3)

        self.play(ShowPaper(paper, direction="DOWN"))
        self.next_slide()

        self.play(PickPage(paper, page_index=2, slide_direction="RIGHT", overshoot=4.0))
        self.next_slide()

        self.play(PickPage(paper, page_index=1, slide_direction="RIGHT", overshoot=4.0))
        self.next_slide()

        self.play(DismissPaper(paper, direction="DOWN"))
        self.next_slide()
