"""Intro slide -- title + bulleted overview."""

from __future__ import annotations

from manim import MathTex, Tex, Title, Unwrite, Write

from simplex.engine.text import color_tex
from simplex.slides import BaseSlide

from utils import FUNCS_COLOR, K_UNIVERSAL_COLOR


class Intro(BaseSlide):
    def construct(self) -> None:
        self.next_slide(name="Intro")
        title = Title("Hash Tables - Intro")
        overview = Tex(
            r"""Overview:
                \begin{itemize}
                    \item[$\bullet$] Hash Tables
                    \item[$\bullet$] Universal Hash Families
                    \begin{itemize}
                    \item examples
                    \end{itemize}
                    \item[$\bullet$] Check Triplets Problem
                    \item[$\bullet$] $k$-Universal Hash Families
                \end{itemize}""",
            tex_environment=r"{minipage}{9.3cm}",
        )
        color_tex(overview, {"k": K_UNIVERSAL_COLOR}, tex_class=MathTex)
        color_tex(overview, {"Hash Tables": FUNCS_COLOR})

        self.play(Write(title))
        self.play(Write(overview))
        self.next_slide()

        self.play(Unwrite(title), Unwrite(overview))
        self.wait()
