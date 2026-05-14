"""Apply theme defaults to vanilla Manim Mobjects."""

from simplex.theme.tokens import Theme


def apply_theme_defaults(theme: Theme) -> None:
    """Set `Mobject.set_default(...)` for every Mobject Simplex cares about."""
    from manim import Arrow, Dot, Line, MathTex, Rectangle, Square, Tex, Text

    tmpl = theme.latex.as_tex_template()
    Tex.set_default(tex_template=tmpl, color=theme.palette.font)
    MathTex.set_default(
        tex_template=tmpl,
        color=theme.palette.font,
        font_size=theme.typography.body,
    )
    Text.set_default(
        color=theme.palette.font,
        font=theme.typography.font_family,
        font_size=theme.typography.body,
    )
    Line.set_default(
        stroke_color=theme.palette.edge,
        stroke_width=theme.spacing.edge_stroke_width,
    )
    Dot.set_default(color=theme.palette.accent)
    Arrow.set_default(stroke_color=theme.palette.edge)
    Rectangle.set_default(stroke_color=theme.palette.edge)
    Square.set_default(stroke_color=theme.palette.edge)
