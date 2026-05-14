"""Code helpers: Darcula Pygments style, code_block factory, highlight + explain.

Targets the modern (post-2024) ``manim.Code`` API:
``Code(code_string=..., language=..., formatter_style=..., paragraph_config=...)``
and the ``code_lines`` attribute. The old ``.code`` / ``.code_json`` /
``.tab_spaces`` plumbing is gone in upstream Manim, so the LaTeX-in-code
rendering from Dastimator's ``compile_code_tex`` is intentionally **not**
ported here -- it would require a re-implementation against Tree-sitter
output, which is out of scope for the framework's first cut.
"""

import sys
import types
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
from pygments.style import Style
from pygments.token import Comment, Generic, Keyword, Literal, Name

from simplex.theme.context import get_active_theme


class DarculaStyle(Style):
    """Pygments scheme inspired by JetBrains Darcula, ported from Dastimator."""

    background_color = "#111111"
    highlight_color = "#333333"

    styles = {  # noqa: RUF012 -- pygments declares `styles` as a class attribute.
        Comment.Multiline: "#808080",
        Comment.Preproc: "#808080",
        Comment.Single: "#808080",
        Comment.Special: "bold #808080",
        Comment: "#808080",
        Generic.Deleted: "#CC4040",
        Generic.Emph: "#A9B7C6",
        Generic.Heading: "#999999",
        Generic.Inserted: "#40CC40",
        Generic.Output: "#888888",
        Generic.Prompt: "#555555",
        Generic.Strong: "bold",
        Generic.Subheading: "#aaaaaa",
        Generic.Traceback: "#aa0000",
        Keyword.Constant: "#CC7832",
        Keyword.Declaration: "#CC7832",
        Keyword.Namespace: "#CC7832",
        Keyword.Pseudo: "#CC7832",
        Keyword.Reserved: "#CC7832",
        Keyword.Type: "#A9B7C6 bold",
        Keyword: "#CC7832 bold",
        Literal.Number: "#6897B3",
        Literal.String: "#008080",
        Literal.String.Doc: "#629755",
        Name.Attribute: "#800080",
        Name.Builtin.Pseudo: "#94558D",
        Name.Builtin: "#8888C6",
        Name.Class: "#A9B7C6 bold",
        Name.Constant: "#B200B2",
        Name.Decorator: "#BBB529",
        Name.Entity: "#A9B7C6",
        Name.Exception: "#A9B7C6 bold",
        Name.Function: "#A9B7C6 bold",
        Name.Label: "#A9B7C6 bold",
        Name.Namespace: "#A9B7C6",
        Name.Tag: "#A5C261 bold",
        Name.Variable.Class: "#A9B7C6 bold",
        Name.Variable.Global: "#A9B7C6 bold",
        Name.Variable.Instance: "#A9B7C6",
        Name.Variable: "#A9B7C6",
    }


def register_darcula(style_name: str = "darcula") -> None:
    """Register `DarculaStyle` under `style_name` in Pygments. Idempotent.

    Called automatically by `code_block`. Exposed so users with their own
    Code mobjects can opt into the same palette.
    """
    import pygments.styles

    if style_name in pygments.styles.STYLE_MAP:
        return
    cls_name = DarculaStyle.__name__
    module = types.ModuleType(style_name)
    setattr(module, cls_name, DarculaStyle)
    setattr(pygments.styles, style_name, module)
    sys.modules[f"pygments.styles.{style_name}"] = module
    pygments.styles.STYLE_MAP[style_name] = f"{style_name}::{cls_name}"


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
        background=background,
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
    selected = (
        set(range(1, len(code_lines) + 1)) if lines is None else set(lines)
    )

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
    target = VGroup(*[code_lines[ln - 1] for ln in lines])
    brace = Brace(target, RIGHT, buff=buff, color=color)
    label = Text(explanation, color=color).scale(scale).next_to(brace, RIGHT, buff=buff)

    fade = highlight_code_lines(
        code, lines=lines, off_opacity=off_opacity, indicate=False,
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
            VGroup(*[src_lines[s - 1] for s in srcs]),
            dst_lines[dst_no - 1],
        )
        for dst_no, srcs in grouped.items()
    ]
    return AnimationGroup(*anims, **kwargs)
