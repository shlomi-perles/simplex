"""Code helpers: Darcula Pygments style, code_block factory, highlight + explain.

Wraps :class:`manim.Code` (the Pygments-backed listing) and exposes its
``code_lines`` attribute through small animation helpers.
"""

from typing import Any

from manim import (
    RIGHT,
    SMALL_BUFF,
    AnimationGroup,
    Brace,
    Code,
    GrowFromCenter,
    Indicate,
    Text,
    TransformMatchingShapes,
    VGroup,
    Write,
)

from simplex.theme.context import get_active_theme
from simplex.theme.pygments_style import DarculaStyle, register_darcula

__all__ = ["DarculaStyle", "register_darcula"]


def code_block(
    code: str,
    *,
    language: str = "python",
    background: str = "window",
    formatter_style: str = "darcula",
    paragraph_config: dict[str, Any] | None = None,
    background_config: dict[str, Any] | None = None,
    **kwargs: Any,
) -> Code:
    """Build a `manim.Code` with Darcula highlighting and the theme mono font.

    Authors get vanilla `manim.Code` back -- everything Manim does to that
    class still works (`.code_lines`, `.background`, `.scale_to_fit_width`).
    """
    if formatter_style == "darcula":
        register_darcula(formatter_style)
    theme = get_active_theme()
    paragraph_kwargs: dict[str, Any] = {"font": theme.typography.mono_family}
    paragraph_kwargs.update(paragraph_config or {})
    return Code(
        code_string=code,
        language=language,
        formatter_style=formatter_style,
        background=background,  # type: ignore[arg-type]
        paragraph_config=paragraph_kwargs,
        background_config=background_config,
        **kwargs,
    )


def highlight_code_lines(
    code: Code,
    lines: list[int] | None = None,
    *,
    off_opacity: float = 0.5,
    indicate: bool = True,
    **kwargs: Any,
) -> AnimationGroup | tuple[AnimationGroup, Indicate]:
    """Dim non-selected lines; optionally `Indicate` the selected ones.

    Line numbers are **1-based** to match what users see on screen.
    """
    code_lines = code.code_lines
    selected = set(range(1, len(code_lines) + 1)) if lines is None else set(lines)

    fade_anims = []
    indicated = []
    for line_no, line in enumerate(code_lines, start=1):
        if line_no in selected:
            fade_anims.append(line.animate.set_fill(opacity=1.0))
            if indicate:
                indicated.append(line)
        else:
            fade_anims.append(line.animate.set_fill(opacity=off_opacity))

    fade_group = AnimationGroup(*fade_anims, **kwargs)
    if indicate:
        return fade_group, Indicate(VGroup(*indicated), **kwargs)
    return fade_group


def code_explain(
    code: Code,
    lines: list[int],
    explanation: str,
    *,
    off_opacity: float = 0.5,
    buff: float = SMALL_BUFF,
    color: str | None = None,
    scale: float = 1.0,
    **kwargs: Any,
) -> tuple[VGroup, AnimationGroup]:
    """Brace + explanation text for a (contiguous) range of lines.

    Returns ``(mobject, animation)``. Add the mobject to the scene before
    playing -- this lets callers position / restyle it first.
    """
    theme = get_active_theme()
    color = color or theme.palette.accent
    code_lines = code.code_lines
    target = VGroup(code_lines[ln - 1] for ln in lines)  # type: ignore[arg-type]
    brace = Brace(target, RIGHT, buff=buff, color=color)
    label = Text(explanation, color=color).scale(scale).next_to(brace, RIGHT, buff=buff)

    fade = highlight_code_lines(
        code,
        lines=lines,
        off_opacity=off_opacity,
        indicate=False,
    )
    return VGroup(brace, label), AnimationGroup(
        fade,
        GrowFromCenter(brace),
        Write(label),
        lag_ratio=kwargs.pop("lag_ratio", 1.0),
        **kwargs,
    )


def transform_code_lines(
    src: Code,
    dst: Code,
    mapping: dict[int, int],
    **kwargs: Any,
) -> AnimationGroup:
    """`TransformMatchingShapes` between matching (1-based) line numbers.

    ``mapping`` is ``{src_line_no: dst_line_no}``. Multiple source lines may
    map to the same destination line (they merge into it).
    """
    src_lines = src.code_lines
    dst_lines = dst.code_lines
    grouped: dict[int, list[int]] = {}
    for s, d in mapping.items():
        grouped.setdefault(d, []).append(s)

    anims = [
        TransformMatchingShapes(
            VGroup(src_lines[s - 1] for s in srcs),  # type: ignore[arg-type]
            dst_lines[dst_no - 1],
        )
        for dst_no, srcs in grouped.items()
    ]
    return AnimationGroup(*anims, **kwargs)
