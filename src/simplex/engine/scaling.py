"""Multi-axis scaling helpers.

Manim ships per-axis `scale_to_fit_width` / `_height` / `_depth` and a
plain `scale`. These helpers add: (a) fitting against multiple target
lengths simultaneously while keeping aspect, plus a buffer; (b) a scale
that compensates the stroke width so a thin line stays a thin line.
"""

from typing import Any

import numpy as np
from manim import Mobject


def scale_with_stroke_width(
    mobject: Mobject,
    scale_factor: float = 1.0,
    *,
    scale_stroke_width: bool = True,
) -> Mobject:
    """`mobject.scale(...)` that also rescales the stroke width across the family."""
    if scale_stroke_width:
        for sub in mobject.get_family():
            sub.set_stroke(width=sub.get_stroke_width() * scale_factor)
    mobject.scale(scale_factor)
    return mobject


def scale_to_fit(
    mobject: Mobject,
    *,
    len_x: float | None = None,
    len_y: float | None = None,
    len_z: float | None = None,
    buff: float = 0.0,
    scaleback: float = 1.0,
    min_scale: float | None = None,
    max_scale: float | None = None,
    scale_stroke_width: bool = False,
) -> Mobject:
    """Uniformly scale `mobject` so it fits inside any subset of the given lengths.

    The smallest required scale is applied (preserves aspect ratio).
    `buff` is subtracted from each target length, `scaleback` shrinks the
    final factor, and the result is clamped by `min_scale` / `max_scale`.
    """
    targets = [length if length and length > 1e-6 else None for length in (len_x, len_y, len_z)]
    sizes = [mobject.get_width(), mobject.get_height(), mobject.get_depth()]
    factors: list[float] = []
    for dim in range(3):
        target = targets[dim]
        if target is None:
            continue
        factor = (target - 2 * buff) / sizes[dim] * scaleback
        factor = float(np.clip(factor, min_scale, max_scale))
        factors.append(factor)
    if not factors:
        return mobject
    return scale_with_stroke_width(mobject, min(factors), scale_stroke_width=scale_stroke_width)


def scale_to_fit_mobject(
    mobject: Mobject,
    other: Mobject,
    **kwargs: Any,
) -> Mobject:
    """Scale `mobject` to fit inside the bounding box of `other`."""
    return scale_to_fit(
        mobject,
        len_x=other.get_width(),
        len_y=other.get_height(),
        len_z=other.get_depth(),
        **kwargs,
    )


__all__ = ["scale_to_fit", "scale_to_fit_mobject", "scale_with_stroke_width"]
