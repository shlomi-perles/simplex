"""Apply theme defaults to vanilla Manim Mobjects."""

from simplex.theme.tokens import Theme


def code_theme_defaults(theme: Theme) -> tuple[str, dict[str, object], dict[str, object]]:
    """Return Manim ``Code`` defaults derived from one Simplex theme."""
    from simplex.theme.pygments_style import (
        background_color_for_style,
        register_style,
        style_name_for_class,
    )

    code_style = theme.code_style
    register_style(code_style)
    return (
        style_name_for_class(code_style),
        {"font": theme.typography.mono_family},
        {
            "fill_color": background_color_for_style(code_style),
            "stroke_color": theme.palette.edge,
            "fill_opacity": 1,
        },
    )


def apply_theme_defaults(theme: Theme) -> None:
    """Set `Mobject.set_default(...)` for every Mobject Simplex cares about."""
    from manim import (
        Arrow,
        Code,
        DecimalNumber,
        Dot,
        Integer,
        Line,
        MarkupText,
        MathTex,
        Paragraph,
        Rectangle,
        Square,
        Tex,
        Text,
        Variable,
    )

    tmpl = theme.latex.as_tex_template()
    formatter_style, paragraph_config, background_config = code_theme_defaults(theme)
    Tex.set_default(
        tex_template=tmpl,
        color=theme.palette.font,
        font_size=theme.typography.body,
    )
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
    MarkupText.set_default(
        color=theme.palette.font,
        font=theme.typography.font_family,
        font_size=theme.typography.body,
    )
    Paragraph.set_default(
        color=theme.palette.font,
        font=theme.typography.font_family,
        font_size=theme.typography.body,
    )
    DecimalNumber.set_default(
        color=theme.palette.font,
        font_size=theme.typography.body,
    )
    Integer.set_default(
        color=theme.palette.font,
        font_size=theme.typography.body,
    )
    Variable.set_default(color=theme.palette.font)
    Line.set_default(
        stroke_color=theme.palette.edge,
        stroke_width=theme.spacing.edge_stroke_width,
    )
    Dot.set_default(color=theme.palette.accent)
    Arrow.set_default(stroke_color=theme.palette.edge)
    Rectangle.set_default(stroke_color=theme.palette.edge)
    Square.set_default(stroke_color=theme.palette.edge)
    Code.set_default(
        formatter_style=formatter_style,
        paragraph_config=paragraph_config,
        background_config=background_config,
    )
