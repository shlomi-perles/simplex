"""Array mobject ported from Dastimator."""

from typing import Any

from manim import RIGHT, MathTex, Rectangle, VGroup, VMobject

from simplex.theme.context import get_active_theme


class ArrayMob(VMobject):
    """A row of equal-sized cells, each holding centered MathTex content."""

    def __init__(
        self,
        values: list[str],
        cell_size: float = 0.8,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        theme = get_active_theme()
        cells = VGroup()
        for value in values:
            cell = Rectangle(
                width=cell_size,
                height=cell_size,
                stroke_color=theme.palette.edge,
                stroke_width=theme.spacing.edge_stroke_width / 2,
            )
            text = MathTex(value, color=theme.palette.font).scale(0.6)
            text.move_to(cell.get_center())
            cells.add(VGroup(cell, text))
        cells.arrange(RIGHT, buff=0)
        self.add(cells)
