"""Multi-axis scaling helpers.

Manim ships per-axis `scale_to_fit_width` / `_height` / `_depth` and a
plain `scale`. These helpers add fitting against multiple target lengths
simultaneously while keeping aspect, plus a buffer.

Stroke-aware scaling uses Manim 0.19+'s native
``mob.scale(factor, scale_stroke=True)`` -- no custom helper needed.
"""

from typing import Any

import numpy as np

from simplex.engine.opengl_compat import MobjectLike, is_vmobject


def scale_to_fit[MobjectT: MobjectLike](
    mobject: MobjectT,
    *,
    len_x: float | None = None,
    len_y: float | None = None,
    len_z: float | None = None,
    buff: float = 0.0,
    scaleback: float = 1.0,
    min_scale: float | None = None,
    max_scale: float | None = None,
    scale_stroke: bool = False,
) -> MobjectT:
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
    factor = min(factors)
    if scale_stroke and is_vmobject(mobject):
        mobject.scale(factor, scale_stroke=True)
    else:
        mobject.scale(factor)
    return mobject


def scale_to_fit_mobject[MobjectT: MobjectLike](
    mobject: MobjectT,
    other: MobjectLike,
    **kwargs: Any,
) -> MobjectT:
    """Scale `mobject` to fit inside the bounding box of `other`."""
    return scale_to_fit(
        mobject,
        len_x=other.get_width(),
        len_y=other.get_height(),
        len_z=other.get_depth(),
        **kwargs,
    )


__all__ = ["scale_to_fit", "scale_to_fit_mobject"]
