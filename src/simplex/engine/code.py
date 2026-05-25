"""Code helpers: themed Pygments style, code_block factory, highlight + explain.

Wraps :class:`manim.Code` (the Pygments-backed listing) and exposes its
``code_lines`` attribute through small animation helpers.

``inline_math_in_code`` / ``code_with_math`` rewrite ``$...$`` regions in
each line into rendered ``MathTex`` glyphs after Pygments has already
highlighted the surrounding code. This is the modern replacement for the
old Simplex ``compile_code_tex`` helper -- it relies on Manim
0.20.x's ``Code.code_lines`` glyph order and reflows each line so the
math width drives the final layout.
"""

import functools
import re
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any, cast

from manim import (
    LEFT,
    RIGHT,
    SMALL_BUFF,
    Animation,
    AnimationGroup,
    Brace,
    Code,
    GrowFromCenter,
    Indicate,
    MathTex,
    SurroundingRectangle,
    Text,
    TransformMatchingShapes,
    VGroup,
    VMobject,
    Write,
)

from simplex.theme.context import get_active_theme
from simplex.theme.pygments_style import register_style

__all__ = ["HighlightResult"]

_INLINE_MATH_PATTERN = re.compile(r"\$([^$\n]+)\$")


@dataclass(frozen=True)
class HighlightResult:
    """Return value of :func:`highlight_code_lines`.

    ``fade`` is always present. ``indicate`` is ``None`` when the caller
    passed ``indicate=False``. Iterable so the prior tuple-style call
    ``self.play(*highlight_code_lines(...))`` keeps working.
    """

    fade: AnimationGroup
    indicate: Indicate | None = None

    def __iter__(self) -> Iterator[Animation]:
        yield self.fade
        if self.indicate is not None:
            yield self.indicate


def _resolve_formatter_style(formatter_style: str | None) -> str:
    """Return the Pygments style name, registering the theme's code style if needed."""
    theme = get_active_theme()
    if formatter_style is not None:
        return formatter_style
    style_cls = theme.code_style
    register_style(style_cls)
    from simplex.theme.pygments_style import _class_name_to_style_name

    return _class_name_to_style_name(style_cls.__name__)


def code_block(
    code: str,
    *,
    language: str = "python",
    background: str = "window",
    formatter_style: str | None = None,
    paragraph_config: dict[str, Any] | None = None,
    background_config: dict[str, Any] | None = None,
    **kwargs: Any,
) -> Code:
    """Build a ``manim.Code`` with the active theme's code style and mono font.

    Authors get vanilla ``manim.Code`` back -- everything Manim does to
    that class still works (``.code_lines``, ``.background``,
    ``.scale_to_fit_width``).
    """
    resolved = _resolve_formatter_style(formatter_style)
    theme = get_active_theme()
    paragraph_kwargs: dict[str, Any] = {"font": theme.typography.mono_family}
    paragraph_kwargs.update(paragraph_config or {})
    return Code(
        code_string=code,
        language=language,
        formatter_style=resolved,
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
) -> HighlightResult:
    """Dim non-selected lines; optionally ``Indicate`` the selected ones.

    Line numbers are **1-based** to match what users see on screen.

    Returns a :class:`HighlightResult` with ``fade`` (always an
    ``AnimationGroup``) and ``indicate`` (an ``Indicate`` instance when
    ``indicate=True``, otherwise ``None``). Iterate to splat into
    ``self.play(*result)``.
    """
    code_lines = code.code_lines
    selected = set(range(1, len(code_lines) + 1)) if lines is None else set(lines)

    fade_anims: list[Animation] = []
    indicated: list[Any] = []
    for line_no, line in enumerate(code_lines, start=1):
        if line_no in selected:
            fade_anims.append(cast(Animation, line.animate.set_fill(opacity=1.0)))
            if indicate:
                indicated.append(line)
        else:
            fade_anims.append(cast(Animation, line.animate.set_fill(opacity=off_opacity)))

    fade_group = AnimationGroup(*fade_anims, **kwargs)
    if not indicate:
        return HighlightResult(fade=fade_group)
    return HighlightResult(
        fade=fade_group,
        indicate=Indicate(VGroup(*indicated), **kwargs),
    )


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

    highlight = highlight_code_lines(
        code,
        lines=lines,
        off_opacity=off_opacity,
        indicate=False,
    )
    return VGroup(brace, label), AnimationGroup(
        highlight.fade,
        GrowFromCenter(brace),
        Write(label),
        lag_ratio=kwargs.pop("lag_ratio", 1.0),
        **kwargs,
    )


def code_with_math(
    code: str,
    *,
    language: str = "python",
    bold_math: bool = False,
    math_color: str | None = None,
    formatter_style: str | None = None,
    **kwargs: Any,
) -> Code:
    """``code_block`` + inline LaTeX for any ``$...$`` regions in ``code``.

    Each ``$expr$`` segment is rewritten into a ``MathTex(expr)`` glyph
    matched to the surrounding text height; the line is then reflowed so
    subsequent glyphs sit flush against the math. The background is
    re-fitted to the new line widths, preserving the original padding.

    The math syntax is identical to :class:`manim.MathTex`. Inline math
    cannot span line breaks; an unmatched ``$`` is left as a literal
    dollar sign by Pygments. Set ``bold_math=True`` to wrap each match
    in ``\\boldsymbol{...}``.
    """
    block = code_block(
        code,
        language=language,
        formatter_style=formatter_style,
        **kwargs,
    )
    return inline_math_in_code(
        block,
        code,
        bold_math=bold_math,
        math_color=math_color,
    )


def inline_math_in_code(
    code: Code,
    source: str,
    *,
    bold_math: bool = False,
    math_color: str | None = None,
) -> Code:
    """Rewrite ``$...$`` regions in an existing ``Code`` block to ``MathTex``.

    Pass the same string that was given to :class:`manim.Code` -- the
    function needs it to locate the math spans, since ``Code`` does not
    retain its input. Returns the same ``Code`` for chaining.
    """
    lines = source.splitlines() or [""]
    code_lines = code.code_lines
    math_scale = _compute_math_scale(code_lines)
    any_math = False
    for line_idx, line_mob in enumerate(code_lines):
        if line_idx >= len(lines):
            break
        if _inline_math_in_line(
            line_mob,
            lines[line_idx],
            math_scale=math_scale,
            bold_math=bold_math,
            math_color=math_color,
        ):
            any_math = True
    if any_math:
        _refit_background(code)
    return code


def _inline_math_in_line(
    line_mob: VGroup,
    source_line: str,
    *,
    math_scale: float,
    bold_math: bool,
    math_color: str | None,
) -> bool:
    """Replace each ``$...$`` span in ``line_mob`` with a ``MathTex`` glyph.

    Returns ``True`` if any substitution happened so the caller can
    decide whether the surrounding background needs to be refit.

    Matches are processed right-to-left so a substitution on the right
    never invalidates the glyph indices computed for the next one.
    """
    matches = list(_INLINE_MATH_PATTERN.finditer(source_line))
    if not matches:
        return False

    substituted = False
    glyph_for_char = _glyph_positions(source_line)
    for match in reversed(matches):
        g_start, g_end = _glyph_span(glyph_for_char, match.start(), match.end())
        if g_start is None or g_end is None or g_end <= g_start:
            continue
        body = match.group(1)
        tex_str = rf"\boldsymbol{{{body}}}" if bold_math else body
        tex = MathTex(tex_str)
        if math_color is not None:
            tex.set_color(math_color)

        span: VGroup = line_mob[g_start:g_end]  # type: ignore[assignment]
        # Preserve the original whitespace gap between the closing ``$``
        # and the next visible glyph -- ``next_to`` below uses this so a
        # source line like ``$y_i$ and ...`` keeps its space instead of
        # collapsing into ``y_iand``.
        tail_gap = 0.0
        if g_end < len(line_mob):
            tail_gap = line_mob[g_end].get_left()[0] - span[-1].get_right()[0]

        # A single calibrated scale (computed once from the code block)
        # keeps every inline math glyph the same effective font size as
        # the surrounding code, regardless of the math content. ``match
        # _height`` here would inflate symbols like ``\infty`` whose bbox
        # is the symbol alone, and shrink big operators like ``\bigcup``
        # whose bbox already includes large limits.
        tex.scale(math_scale)
        tex.move_to(span, aligned_edge=LEFT)

        # Anchor the tex into the line by replacing the first glyph
        # in-place; the remaining marker glyphs collapse to zero width
        # at the tex's right edge so they don't contribute to
        # ``line_mob.width`` when ``next_to`` reflows the tail below.
        span[0].become(tex)
        anchor_right = span[0].get_right()
        for marker in span[1:]:
            marker.set_opacity(0).stretch_to_fit_width(0).move_to(anchor_right)

        tail = line_mob[g_end:]
        if len(tail) > 0:
            tail.next_to(span[0], RIGHT, buff=max(tail_gap, 0.0))
        substituted = True
    return substituted


def _compute_math_scale(code_lines: VGroup) -> float:
    """Pick a single scale so inline ``MathTex`` matches code font size.

    Uses the tallest code glyph across the block as a cap-height proxy
    and a cached ``MathTex(r"Mq")`` (M for cap height, q for descender)
    as the math-side reference. The ratio is the scale to apply to
    every inline math glyph so x-height, cap-height and descenders line
    up with the code text.
    """
    code_cap = max(
        (glyph.height for line in code_lines for glyph in line),
        default=0.0,
    )
    ref_h = _reference_math_height()
    if code_cap <= 0 or ref_h <= 0:
        return 1.0
    return code_cap / ref_h


@functools.cache
def _reference_math_height() -> float:
    """Cached reference height of a baseline ``MathTex`` calibration glyph.

    LaTeX compilation is expensive; this runs once per process. The
    glyph ``"Mq"`` is chosen for its full vertical extent -- ``M`` sets
    the cap height, ``q`` provides a descender.
    """
    return MathTex(r"Mq").height


def _glyph_positions(source_line: str) -> list[int | None]:
    """Map each source char to its glyph index (or ``None`` for whitespace).

    Manim's ``Code`` strips whitespace from ``code_lines`` glyph order
    while preserving the on-screen indent positionally. We rebuild the
    char-to-glyph mapping by walking the source and counting visible
    chars -- so an indented line of ``    print($x$)`` maps the first
    four chars to ``None`` and ``print`` to glyphs 0..4.
    """
    positions: list[int | None] = []
    visible = 0
    for ch in source_line:
        if ch.isspace():
            positions.append(None)
        else:
            positions.append(visible)
            visible += 1
    return positions


def _glyph_span(
    glyph_for_char: list[int | None],
    char_start: int,
    char_end: int,
) -> tuple[int | None, int | None]:
    """Return (start, end) glyph indices for the half-open char range."""
    start: int | None = None
    end: int | None = None
    for i in range(char_start, min(char_end, len(glyph_for_char))):
        glyph_idx = glyph_for_char[i]
        if glyph_idx is not None:
            start = glyph_idx
            break
    for i in range(min(char_end, len(glyph_for_char)) - 1, char_start - 1, -1):
        glyph_idx = glyph_for_char[i]
        if glyph_idx is not None:
            end = glyph_idx + 1
            break
    return start, end


def _refit_background(code: Code) -> None:
    """Re-fit ``code.background`` to the (possibly resized) contents.

    ``Code`` builds its background once at construction with
    ``SurroundingRectangle`` around the line-number + code-line group
    (plus the macOS-style buttons in ``background="window"`` mode);
    after we shuffle glyph widths and heights the rectangle no longer
    hugs the text. We rebuild it around the same content, preserving
    the original buff, corner radius, stroke / fill styling, and the
    button decorations attached as submobjects of the background.
    """
    background = getattr(code, "background", None)
    if background is None or not isinstance(background, VMobject):
        return
    inner = VGroup(*(m for m in code.submobjects if m is not background))
    if len(inner) == 0:
        return
    # ``window`` backgrounds attach the three macOS-style dots as a
    # child VGroup that visually sits just outside the top-left corner
    # of the rectangle. ``become`` walks the entire family and would
    # collapse those decorations onto the origin, so we detach them
    # before the replacement and re-add them after.
    decorations = list(background.submobjects)
    background.remove(*decorations)
    replacement_config: dict[str, Any] = {
        "buff": getattr(background, "buff", 0.3),
        "stroke_width": background.get_stroke_width(),
        "fill_opacity": background.get_fill_opacity(),
        "corner_radius": getattr(background, "corner_radius", 0.0),
    }
    if (stroke_color := background.get_stroke_color()) is not None:
        replacement_config["color"] = stroke_color
    replacement_config["fill_color"] = background.get_fill_color()
    replacement = SurroundingRectangle(inner, **replacement_config)
    background.become(replacement)
    if decorations:
        background.add(*decorations)


def transform_code_lines(
    src: Code,
    dst: Code,
    mapping: dict[int, int],
    **kwargs: Any,
) -> AnimationGroup:
    """``TransformMatchingShapes`` between matching (1-based) line numbers.

    ``mapping`` is ``{src_line_no: dst_line_no}``. Multiple source lines
    may map to the same destination line (they merge into it).
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
