"""Semantic Tex variants and a shape-matching color helper.

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
from collections.abc import Mapping
from numbers import Real
from typing import Any, ClassVar, cast

import numpy as np
from manim import DEFAULT_FONT_SIZE, LARGE_BUFF, MathTex, Tex, TransformMatchingShapes, VMobject
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
type _TexLike = Tex | MathTex
type _TexClass = type[Tex] | type[MathTex]
type _ProbeCacheKey = tuple[_TexClass, str]

_DISPLAY_MATH_RE = re.compile(r"(\\\[(?:.|\n)*?\\\])", re.DOTALL)
_DISPLAY_LENGTH_NAMES = (
    "abovedisplayskip",
    "belowdisplayskip",
    "abovedisplayshortskip",
    "belowdisplayshortskip",
)
_PROBE_CACHE: dict[_ProbeCacheKey, _TexLike] = {}


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


def _split_display_math(parts: tuple[str, ...]) -> tuple[tuple[str, ...], tuple[int, ...]]:
    rendered: list[str] = []
    equation_indices: list[int] = []

    for part in parts:
        cursor = 0
        for match in _DISPLAY_MATH_RE.finditer(part):
            before = part[cursor : match.start()]
            if before.strip():
                rendered.append(before)
            equation_indices.append(len(rendered))
            rendered.append(match.group(0))
            cursor = match.end()
        tail = part[cursor:]
        if tail.strip():
            rendered.append(tail)

    if not rendered:
        rendered.append("")
    return tuple(rendered), tuple(equation_indices)


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
    Tex parts, so ``page.equation(0)`` returns the first displayed equation.
    ``math_spacing`` accepts one pt value for all display skips, a four-value
    tuple, or a mapping keyed by LaTeX display skip length names.
    """

    page_width: ClassVar[PageWidth | None] = None
    buff: ClassVar[float] = LARGE_BUFF
    split_display_math: ClassVar[bool] = True
    math_spacing: ClassVar[DisplayMathSpacing | None] = None

    def __init__(
        self,
        *parts: str,
        page_width: PageWidth | None = None,
        buff: float | None = None,
        math_spacing: DisplayMathSpacing | None = None,
        split_display_math: bool | None = None,
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
        rendered_parts, equation_indices = (
            _split_display_math(parts) if should_split else (tuple(parts), ())
        )

        spacing = self.math_spacing if math_spacing is None else math_spacing
        spacing_commands = _display_math_spacing_commands(spacing)
        if spacing_commands:
            rendered_parts = (f"{spacing_commands}\n{rendered_parts[0]}", *rendered_parts[1:])

        super().__init__(*rendered_parts, **kwargs)
        self.page_width_munits = resolved_page_width
        self.page_buff = resolved_buff
        self.minipage_width_cm = width_cm
        self.equation_part_indices = equation_indices
        self.part_roles = tuple(
            "equation" if index in equation_indices else "text"
            for index in range(len(rendered_parts))
        )

    @property
    def equations(self) -> tuple[VMobject, ...]:
        """Display math parts isolated from ``\\[...\\]`` blocks."""
        return tuple(cast(VMobject, self[index]) for index in self.equation_part_indices)

    def equation(self, index: int) -> VMobject:
        """Return the ``index``-th display equation mobject."""
        return self.equations[index]


def _flatten_points(parts: list[VMobject]) -> VMobject:
    out = VMobject()
    out.points = np.concatenate([p.points for p in parts])
    return out


def search_shape_in_text(text: VMobject, shape: VMobject) -> list[list[slice]]:
    """Find every occurrence of ``shape`` inside ``text`` by shape-key matching.

    Returns one list of slices per line of ``text``. Useful for selective coloring
    where you don't want to re-render the equation.
    """
    key = TransformMatchingShapes.get_mobject_key
    target_len = len(shape.submobjects[0])
    target_key = key(_flatten_points(list(shape.submobjects[0])))
    results: list[list[slice]] = []
    for line in text.submobjects:
        hits: list[slice] = []
        glyphs = list(line)
        for i in range(len(glyphs) - target_len + 1):
            window = _flatten_points(glyphs[i : i + target_len])
            if key(window) == target_key:
                hits.append(slice(i, i + target_len))
        results.append(hits)
    return results


def _build_probe(tex_class: _TexClass, substring: str) -> _TexLike:
    key = (tex_class, substring)
    probe = _PROBE_CACHE.get(key)
    if probe is None:
        probe = tex_class(substring)
        _PROBE_CACHE[key] = probe
    return probe


def _resolve_tex_class(equation: _TexLike) -> _TexClass:
    return type(equation)


def color_tex[TexLikeT: (Tex, MathTex)](
    equation: TexLikeT,
    t2c: Mapping[str, ParsableManimColor],
    *,
    tex_class: _TexClass | None = None,
) -> TexLikeT:
    """Color substrings of a rendered Tex/MathTex by shape-matching probes.

    Example::

        eq = MathTex(r\"a^2 + b^2 = c^2\")
        color_tex(eq, {\"a\": \"#FF6B6B\", \"b\": \"#4ECDC4\", \"c\": \"#FFD93D\"})

    Returns ``equation`` so callers can chain.
    """
    resolved_tex_class = tex_class if tex_class is not None else _resolve_tex_class(equation)
    for substring, color in t2c.items():
        probe = _build_probe(resolved_tex_class, substring)
        for line_idx, hits in enumerate(search_shape_in_text(equation, probe)):
            for span in hits:
                equation[line_idx][span].set_color(color)
    return equation
