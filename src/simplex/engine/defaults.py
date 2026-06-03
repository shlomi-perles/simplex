"""Apply theme defaults to vanilla Manim Mobjects."""

from simplex.theme.tokens import Theme


def code_theme_defaults(theme: Theme) -> tuple[str, dict[str, object], dict[str, object]]:
    """Return Manim ``Code`` defaults derived from one Simplex theme."""
    import manim

    from simplex.theme.palettes import MANIM_DEFAULT, apply_manim_palette
    from simplex.theme.pygments_style import (
        background_color_for_style,
        register_style,
        style_name_for_class,
    )

    apply_manim_palette(manim, theme)
    from manim import WHITE

    code_style = theme.code_style
    register_style(code_style)
    background_config: dict[str, object] = {
        "fill_color": background_color_for_style(code_style),
        "fill_opacity": 1,
    }
    if theme.manim_palette not in (None, MANIM_DEFAULT):
        background_config["stroke_color"] = WHITE
    return (
        style_name_for_class(code_style),
        {"font": theme.typography.mono_family},
        background_config,
    )


def apply_theme_defaults(theme: Theme) -> None:
    """Set `Mobject.set_default(...)` for every Mobject Simplex cares about."""
    from simplex.theme.palettes import MANIM_DEFAULT

    formatter_style, paragraph_config, background_config = code_theme_defaults(theme)
    from manim import (
        WHITE,
        Code,
        DecimalNumber,
        Dot,
        Integer,
        Line,
        MarkupText,
        MathTex,
        Paragraph,
        Rectangle,
        Tex,
        Text,
        Variable,
    )

    tmpl = theme.latex.as_tex_template()
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
    if theme.manim_palette in (None, MANIM_DEFAULT):
        Line.set_default()
        Rectangle.set_default()
    else:
        Line.set_default(color=WHITE)
        Rectangle.set_default(color=WHITE)
    Dot.set_default(color=theme.palette.accent)
    Code.set_default(
        formatter_style=formatter_style,
        paragraph_config=paragraph_config,
        background_config=background_config,
    )
