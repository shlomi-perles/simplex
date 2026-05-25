"""Semantic Tex variants and a shape-matching color helper.

Classes (``Caption``, ``TexPage``) inherit from :class:`manim.Tex` so users
get ``isinstance`` checks, per-class ``set_default(...)``, and the rest of
Manim's API without any wrapping. They pick up theme defaults at construction
time via :func:`get_active_theme`.

Plain :class:`manim.Tex` already carries the theme's body font size + color
through :func:`simplex.engine.defaults.apply_theme_defaults` — use it for body
paragraphs. ``Caption`` is the smaller variant for annotations; ``TexPage``
wraps content in a fixed-width ``{minipage}{<width>cm}`` environment for long
prose.
"""

from collections.abc import Mapping
from typing import Any, ClassVar

import numpy as np
from manim import MathTex, Tex, TransformMatchingShapes, VMobject

from simplex.theme.context import get_active_theme


def _minipage_env(width_cm: float) -> str:
    """Render the LaTeX ``tex_environment`` string for a fixed-width minipage."""
    return f"{{minipage}}{{{width_cm}cm}}"


class Caption(Tex):
    """Tex sized for captions / annotations (``theme.typography.caption``)."""

    def __init__(self, *parts: str, **kwargs: Any) -> None:
        theme = get_active_theme()
        kwargs.setdefault("font_size", theme.typography.caption)
        kwargs.setdefault("color", theme.palette.font)
        super().__init__(*parts, **kwargs)


class TexPage(Tex):
    """Tex wrapped in a fixed-width ``{minipage}`` so long prose stays bounded.

    The default page width is **20 cm**. Override per-instance::

        TexPage("…", width_cm=12.0)

    Or per-subclass (useful for a deck-wide "wide page" variant)::

        class WidePage(TexPage):
            width_cm = 16.0
    """

    width_cm: ClassVar[float] = 20.0

    def __init__(self, *parts: str, width_cm: float | None = None, **kwargs: Any) -> None:
        theme = get_active_theme()
        resolved_width = self.width_cm if width_cm is None else width_cm
        kwargs.setdefault("font_size", theme.typography.body)
        kwargs.setdefault("color", theme.palette.font)
        kwargs.setdefault("tex_environment", _minipage_env(resolved_width))
        super().__init__(*parts, **kwargs)


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


def color_tex(
    equation: Tex | MathTex,
    t2c: Mapping[str, str],
    *,
    tex_class: type[Tex] = Tex,
) -> Tex | MathTex:
    """Color substrings of a rendered Tex/MathTex by shape-matching probes.

    Example::

        eq = MathTex(r\"a^2 + b^2 = c^2\")
        color_tex(eq, {\"a\": \"#FF6B6B\", \"b\": \"#4ECDC4\", \"c\": \"#FFD93D\"}, tex_class=MathTex)

    Returns ``equation`` so callers can chain.
    """
    for substring, color in t2c.items():
        probe = tex_class(substring)
        for line_idx, hits in enumerate(search_shape_in_text(equation, probe)):
            for span in hits:
                equation[line_idx][span].set_color(color)
    return equation
