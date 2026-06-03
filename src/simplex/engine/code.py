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
from typing import Any, Literal, cast

import numpy as np
from manim import (
    LEFT,
    RIGHT,
    SMALL_BUFF,
    UP,
    Animation,
    AnimationGroup,
    Brace,
    BraceLabel,
    BraceText,
    Code,
    Dot,
    FadeIn,
    Group,
    GrowFromCenter,
    Indicate,
    MathTex,
    Mobject,
    SurroundingRectangle,
    Tex,
    TransformMatchingShapes,
    VGroup,
    VMobject,
)
from manim.utils.color import ParsableManimColor

from simplex.engine.defaults import code_theme_defaults
from simplex.engine.opengl_compat import is_vmobject
from simplex.theme.context import get_active_theme
from simplex.theme.pygments_style import register_style, style_name_for_class

__all__ = [
    "HighlightResult",
    "code_block",
    "code_explain",
    "code_with_math",
    "highlight_code_lines",
    "inline_math_in_code",
    "pseudocode_block",
    "transform_code_lines",
]

_INLINE_MATH_PATTERN = re.compile(r"\$([^$\n]+)\$")
_HORIZONTAL_RULE_MAX_HEIGHT = 0.05
_HORIZONTAL_RULE_MIN_WIDTH_RATIO = 0.7
_ROW_GAP_SCALE = 0.75
_MIN_ROW_GROUPING_THRESHOLD = 0.12
_LINE_NUMBER_GUTTER_TOLERANCE = 0.16
_LINE_NUMBER_PREFIX_MAX_WIDTH = 0.45
_LINE_NUMBER_GAP_MIN = 0.12


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
    return style_name_for_class(style_cls)


def code_block(
    code: str,
    *,
    language: str = "python",
    background: str = "window",
    formatter_style: str | None = None,
    paragraph_config: dict[str, Any] | None = None,
    background_config: dict[str, Any] | None = None,
    pseudocode: bool = False,
    **kwargs: Any,
) -> Code:
    """Build a ``manim.Code`` with the active theme's code style and mono font.

    Authors get vanilla ``manim.Code`` back -- everything Manim does to
    that class still works (``.code_lines``, ``.background``,
    ``.scale_to_fit_width``). Set ``pseudocode=True`` when ``code`` is a
    LaTeX ``algorithm2e`` body or full ``algorithm`` environment; the result
    is still a ``Code`` object, but its ``code_lines`` are rendered TeX rows.
    """
    if pseudocode:
        return pseudocode_block(
            code,
            background=background,
            formatter_style=formatter_style,
            paragraph_config=paragraph_config,
            background_config=background_config,
            **kwargs,
        )

    resolved = _resolve_formatter_style(formatter_style)
    theme = get_active_theme()
    _, paragraph_kwargs, background_kwargs = code_theme_defaults(theme)
    paragraph_kwargs.update(paragraph_config or {})
    background_kwargs.update(background_config or {})
    return Code(
        code_string=code,
        language=language,
        formatter_style=resolved,
        background=background,  # type: ignore[arg-type]
        paragraph_config=paragraph_kwargs,
        background_config=background_kwargs,
        **kwargs,
    )


def pseudocode_block(
    code: str,
    *,
    caption: str | None = None,
    algorithm_options: str = "H",
    line_index: Literal["numbered", "visible"] = "numbered",
    background: str = "window",
    formatter_style: str | None = None,
    paragraph_config: dict[str, Any] | None = None,
    background_config: dict[str, Any] | None = None,
    tex_config: dict[str, Any] | None = None,
    **kwargs: Any,
) -> Code:
    """Render ``algorithm2e`` pseudocode while preserving the ``Code`` API.

    ``code`` can be either a complete ``\\begin{algorithm}...`` environment
    or just the body, in which case Simplex wraps it in
    ``\\begin{algorithm}[H]`` and adds ``caption`` when supplied.

    By default ``code_lines`` contains the rows that algorithm2e visibly
    numbers, so ``highlight_code_lines(block, [3])`` targets rendered line 3.
    Set ``line_index="visible"`` to index every visible row, including
    captions and unnumbered input/output rows.
    """
    if line_index not in {"numbered", "visible"}:
        raise ValueError('line_index must be either "numbered" or "visible".')

    if kwargs:
        tex_config = dict(tex_config or {})
        tex_config.update(kwargs)

    algorithm_source = _algorithm_environment_source(
        code,
        caption=caption,
        algorithm_options=algorithm_options,
    )
    rendered = _render_algorithm_tex(algorithm_source, tex_config=tex_config)
    all_lines, rules = _algorithm_rows(rendered)
    if len(all_lines) == 0:
        raise ValueError("algorithm2e source rendered no visible pseudocode rows.")

    numbered_lines = _numbered_algorithm_rows(all_lines)
    indexed_lines = (
        all_lines if line_index == "visible" or len(numbered_lines) == 0 else numbered_lines
    )
    return _code_from_algorithm_rows(
        indexed_lines=indexed_lines,
        rendered_lines=all_lines,
        rules=rules,
        background=background,
        formatter_style=formatter_style,
        paragraph_config=paragraph_config,
        background_config=background_config,
    )


def _algorithm_environment_source(
    code: str,
    *,
    caption: str | None,
    algorithm_options: str,
) -> str:
    """Return a full ``algorithm2e`` environment for ``code``."""
    if r"\begin{algorithm" in code:
        return code

    caption_line = "" if caption is None else rf"\caption{{{caption}}}" + "\n"
    body = code.strip("\n")
    return (
        rf"\begin{{algorithm}}[{algorithm_options}]"
        "\n"
        f"{caption_line}"
        f"{body}"
        "\n"
        r"\end{algorithm}"
    )


def _render_algorithm_tex(
    algorithm_source: str,
    *,
    tex_config: dict[str, Any] | None,
) -> Tex:
    """Compile one full algorithm2e environment as a Manim ``Tex`` mobject."""
    theme = get_active_theme()
    tex_kwargs: dict[str, Any] = {
        "tex_environment": None,
        "tex_template": theme.latex.as_tex_template(),
        "color": theme.palette.font,
        "font_size": theme.typography.body,
    }
    tex_kwargs.update(tex_config or {})
    return Tex(algorithm_source, **tex_kwargs)


def _algorithm_rows(rendered: Tex) -> tuple[VGroup, VGroup]:
    """Split rendered algorithm glyphs into visible rows plus rule mobjects."""
    leaves = list(_leaf_mobjects(rendered))
    rule_mobjects = [
        mob for mob in leaves if _is_horizontal_rule(mob, rendered_width=rendered.width)
    ]
    glyphs = [mob for mob in leaves if mob not in rule_mobjects]
    if not glyphs:
        return VGroup(), VGroup(*rule_mobjects)

    positive_heights = [mob.height for mob in glyphs if mob.height > 0]
    median_height = float(np.median(positive_heights)) if positive_heights else 0.0
    threshold = max(median_height * _ROW_GAP_SCALE, _MIN_ROW_GROUPING_THRESHOLD)

    row_buckets: list[list[VMobject]] = []
    row_centers: list[float] = []
    for glyph in sorted(glyphs, key=lambda mob: mob.get_center()[1], reverse=True):
        glyph_y = float(glyph.get_center()[1])
        closest_idx: int | None = None
        closest_distance = float("inf")
        for idx, row_y in enumerate(row_centers):
            distance = abs(row_y - glyph_y)
            if distance < closest_distance:
                closest_idx = idx
                closest_distance = distance
        if closest_idx is None or closest_distance > threshold:
            row_buckets.append([glyph])
            row_centers.append(glyph_y)
            continue

        bucket = row_buckets[closest_idx]
        bucket.append(glyph)
        row_centers[closest_idx] = float(np.mean([mob.get_center()[1] for mob in bucket]))

    rows = [
        VGroup(*sorted(bucket, key=lambda mob: mob.get_left()[0]))
        for _, bucket in sorted(
            zip(row_centers, row_buckets, strict=True),
            key=lambda item: item[0],
            reverse=True,
        )
    ]
    return VGroup(*rows), VGroup(*rule_mobjects)


def _leaf_mobjects(mob: Mobject) -> Iterator[VMobject]:
    """Yield drawable leaves under ``mob`` without returning wrapper groups."""
    if len(mob.submobjects) == 0:
        if len(getattr(mob, "points", ())) > 0:
            yield cast(VMobject, mob)
        return
    for child in mob.submobjects:
        yield from _leaf_mobjects(child)


def _is_horizontal_rule(mob: Mobject, *, rendered_width: float) -> bool:
    """Return whether ``mob`` is an algorithm2e horizontal rule."""
    if rendered_width <= 0:
        return False
    return (
        mob.height <= _HORIZONTAL_RULE_MAX_HEIGHT
        and mob.width >= rendered_width * _HORIZONTAL_RULE_MIN_WIDTH_RATIO
    )


def _numbered_algorithm_rows(rows: VGroup) -> VGroup:
    """Return rows that include algorithm2e's printed line-number gutter."""
    if len(rows) == 0:
        return VGroup()

    global_left = min(row.get_left()[0] for row in rows)
    numbered = [row for row in rows if _row_has_line_number(row, global_left=float(global_left))]
    return VGroup(*numbered)


def _row_has_line_number(row: VGroup, *, global_left: float) -> bool:
    """Detect algorithm2e's left-gutter line number in one rendered row."""
    glyphs = sorted(row, key=lambda mob: mob.get_left()[0])
    if len(glyphs) < 2:
        return False
    row_left = float(glyphs[0].get_left()[0])
    if row_left > global_left + _LINE_NUMBER_GUTTER_TOLERANCE:
        return False

    for idx in range(min(len(glyphs) - 1, 4)):
        prefix_width = float(glyphs[idx].get_right()[0] - glyphs[0].get_left()[0])
        gap = float(glyphs[idx + 1].get_left()[0] - glyphs[idx].get_right()[0])
        if prefix_width <= _LINE_NUMBER_PREFIX_MAX_WIDTH and gap >= _LINE_NUMBER_GAP_MIN:
            return True
    return False


def _code_from_algorithm_rows(
    *,
    indexed_lines: VGroup,
    rendered_lines: VGroup,
    rules: VGroup,
    background: str,
    formatter_style: str | None,
    paragraph_config: dict[str, Any] | None,
    background_config: dict[str, Any] | None,
) -> Code:
    """Build a ``Code`` shell around rendered algorithm rows."""
    resolved = _resolve_formatter_style(formatter_style)
    theme = get_active_theme()
    _, paragraph_kwargs, background_kwargs = code_theme_defaults(theme)
    paragraph_kwargs.update(paragraph_config or {})
    background_kwargs.update(background_config or {})

    shell = Code(
        code_string="x",
        language="text",
        formatter_style=resolved,
        background="rectangle",
        add_line_numbers=False,
        paragraph_config=paragraph_kwargs,
        background_config=background_kwargs,
    )
    shell.remove(*shell.submobjects)
    shell_any = cast(Any, shell)
    shell_any.code_lines = indexed_lines
    shell_any.line_numbers = VGroup()
    shell.add(rendered_lines)
    if len(rules) > 0:
        shell.add(rules)

    shell_any.background = _algorithm_background(
        VGroup(rendered_lines, rules),
        background=background,
        background_config=background_kwargs,
    )
    shell.add_to_back(shell_any.background)
    return shell


def _algorithm_background(
    content: VMobject,
    *,
    background: str,
    background_config: dict[str, Any],
) -> SurroundingRectangle:
    """Create a Manim ``Code``-style background around algorithm content."""
    background_config_base = Code.default_background_config.copy()
    background_config_base.update(background_config)
    if background == "rectangle":
        return SurroundingRectangle(content, **background_config_base)
    if background == "window":
        buttons = VGroup(
            Dot(radius=0.1, stroke_width=0, color=button_color)
            for button_color in ["#ff5f56", "#ffbd2e", "#27c93f"]
        ).arrange(RIGHT, buff=0.1)
        buttons.next_to(content, UP, buff=0.1).align_to(content, LEFT).shift(LEFT * 0.1)
        background_mob = SurroundingRectangle(
            VGroup(content, buttons),
            **background_config_base,
        )
        buttons.shift(UP * 0.1 + LEFT * 0.1)
        background_mob.add(buttons)
        return background_mob
    raise ValueError(f"Unknown background type: {background}")


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
    explanation: str | Mobject,
    *,
    off_opacity: float = 0.5,
    buff: float = SMALL_BUFF,
    color: ParsableManimColor | None = None,
    scale: float = 1.0,
    tex_label: bool = False,
    **kwargs: Any,
) -> tuple[Mobject, AnimationGroup]:
    """Brace + explanation text for a (contiguous) range of lines.

    ``explanation`` can be a string, which produces a Manim ``BraceText``
    (or ``BraceLabel`` when ``tex_label=True``), or a pre-built mobject such
    as ``MathTex``. Custom mobjects are positioned with ``Brace.put_at_tip``.

    Returns ``(mobject, animation)``. Add the mobject to the scene before
    playing -- this lets callers position / restyle it first.
    """
    theme = get_active_theme()
    explicit_color = color is not None
    resolved_color = color or theme.palette.accent
    code_lines = code.code_lines
    # ``lines`` are 1-based and ``code_explain``'s docstring promises a
    # contiguous range, so slice the underlying ``VGroup`` directly --
    # Manim's ``Code.code_lines`` is a ``VGroup`` and supports list-style
    # slicing without rebuilding the group from a generator expression.
    target = code_lines[lines[0] - 1 : lines[-1]]
    label_mobject: Mobject
    label_creation: Animation

    if isinstance(explanation, str):
        brace_config = {"color": resolved_color}
        label_mobject = (
            BraceLabel(
                target,
                explanation,
                brace_direction=RIGHT,
                buff=buff,
                brace_config=brace_config,
            )
            if tex_label
            else BraceText(
                target,
                explanation,
                brace_direction=RIGHT,
                buff=buff,
                brace_config=brace_config,
            )
        )
        label_mobject.label.set_color(resolved_color)
        label_mobject.label.scale(scale)
        label_mobject.brace.put_at_tip(label_mobject.label)
        label_creation = label_mobject.creation_anim()
    else:
        brace = Brace(target, RIGHT, buff=buff, color=resolved_color)
        if explicit_color:
            explanation.set_color(resolved_color)
        explanation.scale(scale)
        brace.put_at_tip(explanation, buff=buff)
        label_mobject = Group(brace, explanation)
        label_creation = AnimationGroup(GrowFromCenter(brace), FadeIn(explanation))

    highlight = highlight_code_lines(
        code,
        lines=lines,
        off_opacity=off_opacity,
        indicate=False,
    )
    return label_mobject, AnimationGroup(
        highlight.fade,
        label_creation,
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

    original_left = line_mob.get_left()[0]
    original_center_y = line_mob.get_center()[1]
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
    if substituted:
        line_mob.shift(
            np.array(
                [
                    original_left - line_mob.get_left()[0],
                    original_center_y - line_mob.get_center()[1],
                    0.0,
                ]
            )
        )
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
    if background is None or not is_vmobject(background):
        return
    inner = VGroup(*(m for m in code.submobjects if m is not background))
    if len(inner) == 0:
        return
    # ``window`` backgrounds attach the three macOS-style dots as a
    # child VGroup that visually sits just outside the top-left corner
    # of the rectangle. ``become`` walks the entire family and would
    # collapse those decorations onto the origin, so we detach them
    # before the replacement and re-add them after.
    background_mobject = cast(Any, background)
    decorations = list(background_mobject.submobjects)
    background_mobject.remove(*decorations)
    replacement_config: dict[str, Any] = {
        "buff": getattr(background, "buff", 0.3),
        "stroke_width": background.get_stroke_width(),
        "fill_opacity": background.get_fill_opacity(),
        "corner_radius": getattr(background, "corner_radius", 0.0),
    }
    if (stroke_color := background.get_stroke_color()) is not None:
        replacement_config["color"] = stroke_color
    replacement_config["fill_color"] = background.get_fill_color()
    bounds = VGroup(inner, *decorations) if decorations else inner
    replacement = SurroundingRectangle(cast(Any, bounds), **replacement_config)
    background_mobject.become(replacement)
    if decorations:
        background_mobject.add(*decorations)


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
            VGroup(*(src_lines[s - 1] for s in srcs)),  # type: ignore[arg-type]
            dst_lines[dst_no - 1],
        )
        for dst_no, srcs in grouped.items()
    ]
    return AnimationGroup(*anims, **kwargs)
