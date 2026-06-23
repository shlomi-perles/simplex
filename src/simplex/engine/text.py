"""Semantic Tex/Text variants and a shape-matching color helper.

Classes (``Caption``, ``TexPage``) inherit from :class:`manim.Tex` so users
get ``isinstance`` checks, per-class ``set_default(...)``, and the rest of
Manim's API without any wrapping. They pick up theme defaults at construction
time via :func:`get_active_theme`.

Plain :class:`manim.Tex` already carries the theme's body font size + color
through :func:`simplex.engine.defaults.apply_theme_defaults` — use it for body
paragraphs. ``Caption`` is the smaller variant for annotations; ``TexPage``
wraps content in a ``{minipage}{<width>cm}`` environment calibrated from Manim
frame units so long prose fits inside a region.
"""

import functools
import re
from collections.abc import Mapping, Sequence
from numbers import Real
from typing import Any, ClassVar

import numpy as np
from manim import (
    DEFAULT_FONT_SIZE,
    LARGE_BUFF,
    MathTex,
    Mobject,
    Tex,
    Text,
    TransformMatchingShapes,
    VGroup,
    VMobject,
)
from manim.utils.color import ParsableManimColor

from simplex.engine.region import Region
from simplex.theme.context import get_active_theme

type DisplayMathSpacing = (
    int
    | float
    | tuple[int | float, int | float, int | float, int | float]
    | Mapping[str, int | float]
)
type PageWidth = int | float | Region
type _TextLike = Text | Tex | MathTex
type _TextClass = type[Text] | type[Tex] | type[MathTex]
type _ProbeCacheKey = tuple[_TextClass, str]

_DISPLAY_MATH_RE = re.compile(r"(\\\[(?:.|\n)*?\\\])", re.DOTALL)
_DISPLAY_LENGTH_NAMES = (
    "abovedisplayskip",
    "belowdisplayskip",
    "abovedisplayshortskip",
    "belowdisplayshortskip",
)
_PROBE_CACHE: dict[_ProbeCacheKey, _TextLike] = {}


def _minipage_env(width_cm: float) -> str:
    """Render the LaTeX ``tex_environment`` string for a fixed-width minipage."""
    return f"{{minipage}}{{{width_cm}cm}}"


def _format_pt(value: float) -> str:
    return f"{value:g}pt"


def _display_math_spacing_commands(spacing: DisplayMathSpacing | None) -> str:
    if spacing is None:
        return ""
    if isinstance(spacing, int | float):
        values = {name: float(spacing) for name in _DISPLAY_LENGTH_NAMES}
    elif isinstance(spacing, tuple):
        if len(spacing) != len(_DISPLAY_LENGTH_NAMES):
            raise ValueError(
                "math_spacing tuple must contain four values: "
                "above, below, above_short, below_short"
            )
        values = dict(zip(_DISPLAY_LENGTH_NAMES, map(float, spacing), strict=True))
    else:
        unknown = set(spacing) - set(_DISPLAY_LENGTH_NAMES)
        if unknown:
            known = ", ".join(_DISPLAY_LENGTH_NAMES)
            bad = ", ".join(sorted(unknown))
            raise ValueError(f"unknown math_spacing key(s): {bad}; expected any of {known}")
        values = {name: float(value) for name, value in spacing.items()}

    return "\n".join(
        rf"\setlength{{\{name}}}{{{_format_pt(values[name])}}}"
        for name in _DISPLAY_LENGTH_NAMES
        if name in values
    )


def _append_line_part(
    rendered: list[str],
    line_indices: list[int],
    text: str,
    *,
    include_empty_lines: bool,
) -> None:
    if not text:
        return
    if include_empty_lines or text.strip():
        line_indices.append(len(rendered))
        rendered.append(text)


def _split_display_math(
    parts: tuple[str, ...],
    *,
    include_empty_lines: bool = False,
) -> tuple[tuple[str, ...], tuple[int, ...], tuple[int, ...]]:
    rendered: list[str] = []
    equation_indices: list[int] = []
    line_indices: list[int] = []

    for part in parts:
        cursor = 0
        for match in _DISPLAY_MATH_RE.finditer(part):
            _append_line_part(
                rendered,
                line_indices,
                part[cursor : match.start()],
                include_empty_lines=include_empty_lines,
            )
            equation_indices.append(len(rendered))
            rendered.append(match.group(0))
            cursor = match.end()
        _append_line_part(
            rendered,
            line_indices,
            part[cursor:],
            include_empty_lines=include_empty_lines,
        )

    if not rendered:
        rendered.append("")
    return tuple(rendered), tuple(equation_indices), tuple(line_indices)


def _unsplit_tex_parts(parts: tuple[str, ...]) -> tuple[tuple[str, ...], tuple[int, ...]]:
    rendered = tuple(part for part in parts if part)
    if not rendered:
        return ("",), ()
    return rendered, tuple(range(len(rendered)))


def _resolve_page_width(page_width: PageWidth | None) -> float:
    if page_width is None:
        return float(Region.full_frame().width)
    if isinstance(page_width, Region):
        return float(page_width.width)
    if isinstance(page_width, Real):
        return float(page_width)
    raise TypeError("page_width must be a number, Region, or None")


@functools.lru_cache(maxsize=64)
def munits_per_cm(font_size: float = DEFAULT_FONT_SIZE) -> float:
    """Return how many Manim units wide one LaTeX minipage cm is."""
    probe = Tex(
        r"\rule{1cm}{1pt}",
        tex_environment=_minipage_env(1.0),
        font_size=font_size,
    )
    return float(probe.width)


def minipage_cm_for_page_width(
    page_width: PageWidth | None = None,
    font_size: float = DEFAULT_FONT_SIZE,
) -> float:
    """Convert a Manim-unit page width to a LaTeX minipage width in cm."""
    resolved_width = _resolve_page_width(page_width)
    if resolved_width <= 0:
        raise ValueError(f"page_width must be positive, got {resolved_width}")
    return resolved_width / munits_per_cm(font_size)


class Caption(Tex):
    """Tex sized for captions / annotations (``theme.typography.caption``).

    The font color is left to ``Tex.set_default(color=...)`` (configured by
    :func:`simplex.engine.defaults.apply_theme_defaults`); only the smaller
    caption font size is overridden here.
    """

    def __init__(self, *parts: str, **kwargs: Any) -> None:
        kwargs.setdefault("font_size", get_active_theme().typography.caption)
        super().__init__(*parts, **kwargs)


class TexPage(Tex):
    """Tex wrapped in a calibrated ``{minipage}`` so long prose stays bounded.

    By default, the page width is the current full-frame width minus
    ``2 * LARGE_BUFF``. Override per-instance with a number of Manim units or
    a :class:`Region`::

        TexPage("...", page_width=my_region, buff=0.4)

    Display math blocks delimited by ``\\[...\\]`` are split into their own
    Tex parts, so ``page.equation(0)`` returns the first displayed equation
    and ``page.line(0)`` returns the first non-equation chunk. Set
    ``include_empty_lines=True`` to keep blank/newline-only chunks between
    equations addressable too. ``math_spacing`` accepts one pt value for all
    display skips, a four-value tuple, or a mapping keyed by LaTeX display
    skip length names.
    """

    page_width: ClassVar[PageWidth | None] = None
    buff: ClassVar[float] = LARGE_BUFF
    split_display_math: ClassVar[bool] = True
    include_empty_lines: ClassVar[bool] = False
    math_spacing: ClassVar[DisplayMathSpacing | None] = None

    def __init__(
        self,
        *parts: str,
        page_width: PageWidth | None = None,
        buff: float | None = None,
        math_spacing: DisplayMathSpacing | None = None,
        split_display_math: bool | None = None,
        include_empty_lines: bool | None = None,
        **kwargs: Any,
    ) -> None:
        if "width_cm" in kwargs:
            raise TypeError("TexPage uses page_width=...; width_cm was removed")

        font_size = float(kwargs.get("font_size", get_active_theme().typography.body))
        resolved_page_width = _resolve_page_width(
            self.page_width if page_width is None else page_width
        )
        resolved_buff = self.buff if buff is None else float(buff)
        usable_width = resolved_page_width - 2 * resolved_buff
        if usable_width <= 0:
            raise ValueError(
                "page_width minus 2 * buff must be positive; "
                f"got page_width={resolved_page_width}, buff={resolved_buff}"
            )
        width_cm = minipage_cm_for_page_width(usable_width, font_size=font_size)
        kwargs.setdefault("tex_environment", _minipage_env(width_cm))

        should_split = self.split_display_math if split_display_math is None else split_display_math
        should_include_empty_lines = (
            self.include_empty_lines if include_empty_lines is None else include_empty_lines
        )
        if should_split:
            rendered_parts, equation_indices, line_indices = _split_display_math(
                parts,
                include_empty_lines=should_include_empty_lines,
            )
        else:
            rendered_parts, line_indices = _unsplit_tex_parts(parts)
            equation_indices = ()

        spacing = self.math_spacing if math_spacing is None else math_spacing
        spacing_commands = _display_math_spacing_commands(spacing)
        if spacing_commands:
            rendered_parts = (f"{spacing_commands}\n{rendered_parts[0]}", *rendered_parts[1:])

        super().__init__(*rendered_parts, **kwargs)
        self.page_width_munits = resolved_page_width
        self.page_buff = resolved_buff
        self.minipage_width_cm = width_cm
        self.equation_part_indices = equation_indices
        self.line_part_indices = line_indices
        self.part_roles = tuple(
            "equation" if index in equation_indices else "text"
            for index in range(len(rendered_parts))
        )

    @property
    def lines(self) -> tuple[VMobject, ...]:
        """Non-equation Tex parts between display equations."""
        return tuple(_require_vmobject(self[index]) for index in self.line_part_indices)

    def line(self, index: int) -> VMobject:
        """Return the ``index``-th non-equation Tex part."""
        return self.lines[index]

    @property
    def equations(self) -> tuple[VMobject, ...]:
        """Display math parts isolated from ``\\[...\\]`` blocks."""
        return tuple(_require_vmobject(self[index]) for index in self.equation_part_indices)

    def equation(self, index: int) -> VMobject:
        """Return the ``index``-th display equation mobject."""
        return self.equations[index]


def _require_vmobject(mobject: Mobject) -> VMobject:
    if not isinstance(mobject, VMobject):
        raise TypeError(f"{type(mobject).__name__} is not a VMobject")
    return mobject


def _vmobject_children(mobject: VMobject) -> tuple[VMobject, ...]:
    return tuple(_require_vmobject(child) for child in mobject.submobjects)


def _glyph_lines(mobject: VMobject) -> tuple[tuple[VMobject, ...], ...]:
    """Return glyph sequences for Tex/MathTex parts and flat Text objects."""
    children = _vmobject_children(mobject)
    if not children:
        return ()
    if all(len(child.submobjects) == 0 for child in children):
        return (children,)
    return tuple(_vmobject_children(child) for child in children)


def _flatten_points(parts: Sequence[VMobject]) -> VMobject:
    out = VMobject()
    point_arrays = [p.points for p in parts if len(p.points) > 0]
    out.points = np.concatenate(point_arrays) if point_arrays else np.empty((0, 3))
    return out


def _first_glyph_line(mobject: VMobject) -> tuple[VMobject, ...]:
    for glyphs in _glyph_lines(mobject):
        if glyphs:
            return glyphs
    return ()


def _shape_spans(glyphs: Sequence[VMobject], target_glyphs: Sequence[VMobject]) -> list[slice]:
    target_len = len(target_glyphs)
    if target_len == 0:
        return []

    key = TransformMatchingShapes.get_mobject_key
    target_key = key(_flatten_points(target_glyphs))
    hits: list[slice] = []
    for i in range(len(glyphs) - target_len + 1):
        window = _flatten_points(glyphs[i : i + target_len])
        if key(window) == target_key:
            hits.append(slice(i, i + target_len))
    return hits


def search_shape_in_text(text: VMobject, shape: VMobject) -> list[list[slice]]:
    """Find every occurrence of ``shape`` inside ``text`` by shape-key matching.

    Returns one list of slices per line of ``text``. Useful for selective coloring
    where you don't want to re-render the equation.
    """
    target_glyphs = _first_glyph_line(shape)
    return [_shape_spans(glyphs, target_glyphs) for glyphs in _glyph_lines(text)]


def _build_probe(
    text_class: _TextClass,
    substring: str,
    *,
    probe_config: Mapping[str, Any] | None,
) -> _TextLike:
    if probe_config:
        return text_class(substring, **dict(probe_config))

    key = (text_class, substring)
    probe = _PROBE_CACHE.get(key)
    if probe is None:
        probe = text_class(substring)
        _PROBE_CACHE[key] = probe
    return probe


def _resolve_text_class(mobject: _TextLike) -> _TextClass:
    return type(mobject)


def color_substrings[TextLikeT: (Text, Tex, MathTex)](
    mobject: TextLikeT,
    colors: Mapping[str, ParsableManimColor],
    *,
    probe_class: _TextClass | None = None,
    probe_config: Mapping[str, Any] | None = None,
) -> TextLikeT:
    """Color substrings of rendered Text/Tex/MathTex by shape-matching probes.

    Example::

        eq = MathTex(r\"a^2 + b^2 = c^2\")
        color_substrings(eq, {\"a\": \"#FF6B6B\", \"b\": \"#4ECDC4\", \"c\": \"#FFD93D\"})

    Text probes should use the same font family/weight as the target text.
    Pass ``probe_config`` for non-default ``Text`` styling.

    Returns ``mobject`` so callers can chain.
    """
    resolved_probe_class = probe_class if probe_class is not None else _resolve_text_class(mobject)
    glyph_lines = _glyph_lines(mobject)
    for substring, color in colors.items():
        probe = _build_probe(
            resolved_probe_class,
            substring,
            probe_config=probe_config,
        )
        target_glyphs = _first_glyph_line(probe)
        for glyphs in glyph_lines:
            hits = _shape_spans(glyphs, target_glyphs)
            for span in hits:
                VGroup(*glyphs[span]).set_color(color)
    return mobject
