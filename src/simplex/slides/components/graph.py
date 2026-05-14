"""Graph mobjects (Node, Edge) ported from Dastimator."""

from typing import Any

from manim import Circle, Line, MathTex, ShrinkToCenter, VMobject

from simplex.engine.animations import set_exit_animation
from simplex.theme.context import get_active_theme


class Node(VMobject):
    """Filled circle with a centered MathTex label."""

    def __init__(self, label: str | int = "", radius: float = 0.35, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        theme = get_active_theme()
        circle = Circle(
            radius=radius,
            fill_color=theme.palette.vertex,
            fill_opacity=1.0,
            stroke_color=theme.palette.vertex_stroke,
            stroke_width=theme.spacing.vertex_stroke_width,
        )
        text = MathTex(str(label), color=theme.palette.label).scale(0.9)
        text.move_to(circle.get_center())
        self.add(circle, text)
        set_exit_animation(self, ShrinkToCenter)


class Edge(VMobject):
    """Line between two anchors, with an optional weight label at the midpoint."""

    def __init__(
        self,
        start: Any,
        end: Any,
        weight: str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        theme = get_active_theme()
        a = start.get_center() if hasattr(start, "get_center") else start
        b = end.get_center() if hasattr(end, "get_center") else end
        line = Line(
            a,
            b,
            color=theme.palette.edge,
            stroke_width=theme.spacing.edge_stroke_width,
        )
        self.add(line)
        if weight is not None:
            label = MathTex(weight, color=theme.palette.weight).scale(0.4)
            label.move_to(line.get_center())
            self.add(label)
