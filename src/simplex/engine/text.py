"""Semantic Tex variants and a shape-matching color helper.

Classes (BodyText, Caption, Definition) inherit from `manim.Tex` so users get
`isinstance` checks, per-class `set_default(...)`, and the rest of Manim's API
without any wrapping. They pick up theme defaults at construction time via
`get_active_theme()`.
"""

from collections.abc import Mapping
from typing import Any

import numpy as np
from manim import MathTex, Tex, TransformMatchingShapes, VMobject

from simplex.theme.context import get_active_theme


class BodyText(Tex):
    """Tex sized for body paragraphs (theme.typography.body).

    Authors write inline math the usual way: ``BodyText(r\"$E=mc^2$ is...\")``.
    """

    def __init__(self, *parts: str, **kwargs: Any) -> None:
        theme = get_active_theme()
        kwargs.setdefault("font_size", theme.typography.body)
        kwargs.setdefault("color", theme.palette.font)
        super().__init__(*parts, **kwargs)


class Caption(Tex):
    """Tex sized for captions / annotations (theme.typography.caption)."""

    def __init__(self, *parts: str, **kwargs: Any) -> None:
        theme = get_active_theme()
        kwargs.setdefault("font_size", theme.typography.caption)
        kwargs.setdefault("color", theme.palette.font)
        super().__init__(*parts, **kwargs)


class Definition(Tex):
    """Tex wrapped in the theme's ``definition`` environment.

    DASTIMATOR_DARK seeds this to ``{minipage}{8cm}`` so long prose stays
    inside a fixed width. Override at the theme level, not on the call site::

        Theme(..., latex=LatexProfile(environments={\"definition\": \"{minipage}{10cm}\"}))
    """

    def __init__(self, *parts: str, **kwargs: Any) -> None:
        theme = get_active_theme()
        env = theme.latex.environments.get("definition", "{minipage}{8cm}")
        kwargs.setdefault("font_size", theme.typography.body)
        kwargs.setdefault("color", theme.palette.font)
        kwargs.setdefault("tex_environment", env)
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
