"""Minimal OutlineScene demo."""

from manim import Circle, Square, Triangle

from simplex import Caption, OutlinePart, OutlineScene, TexPage


class OutlineDemo(OutlineScene):
    def __init__(self, **kwargs):
        parts = [
            OutlinePart(
                title=TexPage(r"Research Question"),
                label=Caption(r"Research\\Question"),
                visual=Circle(),
            ),
            OutlinePart(
                title=TexPage(r"Low-Rank Algorithms"),
                label=Caption("Algorithms"),
                visual=Square(),
            ),
            OutlinePart(
                title=TexPage(r"Case Study"),
                label=Caption(r"Case\\Study"),
                visual=Triangle(),
            ),
        ]
        super().__init__(parts=parts, section_name="Outline Demo", **kwargs)
