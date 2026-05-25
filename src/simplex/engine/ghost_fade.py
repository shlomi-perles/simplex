"""``GhostSlideFade`` -- fade in, drift, fade out, self-cleanup.

Single-mobject in-place animation: fade in, optionally drift / scale /
rotate during a configurable lifetime, then fade out. The mobject is
removed from the scene on cleanup so callers can spawn ghost cues
without later teardown bookkeeping.

Sibling of ``TransformByGlyphMap`` (see ``glyph_map.py``); split into its
own module to keep each file focused on one Animation class.
"""

from typing import Any

import numpy as np
from manim import ORIGIN, Animation, Mobject


class GhostSlideFade(Animation):
    """Fade a mobject in, optionally drift / scale / rotate it, then fade out.

    Self-contained: removes the mobject from the scene on cleanup, so
    callers can spawn ghost cues without later teardown bookkeeping.
    """

    def __init__(  # pyright: ignore[reportInconsistentConstructor]
        self,
        mob: Mobject,
        *,
        scale_factor: float = 1.0,
        shift_vector: np.ndarray = ORIGIN,
        rotate_amount: float = 0.0,
        fade_in_time: float = 1.0,
        fade_out_time: float = 1.0,
        lifetime: float = 3.0,
        living_stroke_opacity: float = 1.0,
        living_fill_opacity: float = 0.0,
        **kwargs: Any,
    ) -> None:
        self.mobject = mob
        self.scale_factor = scale_factor
        self.shift_vector = shift_vector
        self.rotate_amount = rotate_amount
        self.fade_in_time = fade_in_time
        self.fade_out_time = fade_out_time
        self.lifetime = lifetime
        self.living_stroke_opacity = living_stroke_opacity
        self.living_fill_opacity = living_fill_opacity
        kwargs.setdefault("run_time", fade_in_time + lifetime + fade_out_time)
        super().__init__(mob, **kwargs)

    def clean_up_from_scene(self, scene: Any) -> None:
        super().clean_up_from_scene(scene)
        scene.remove(self.mobject)

    def interpolate_mobject(self, alpha: float) -> None:
        alpha = self.rate_func(alpha)
        total = self.fade_in_time + self.lifetime + self.fade_out_time
        self.mobject.become(self.starting_mobject)
        self.mobject.scale(self.scale_factor**alpha)
        self.mobject.shift(self.shift_vector * alpha)
        self.mobject.rotate(self.rotate_amount * alpha, about_point=self.mobject.get_center())
        in_frac = self.fade_in_time / total
        out_frac = 1 - self.fade_out_time / total
        if alpha <= in_frac:
            factor = alpha / in_frac if in_frac > 0 else 1.0
        elif alpha >= out_frac:
            tail = self.fade_out_time / total
            factor = (1 - alpha) / tail if tail > 0 else 0.0
        else:
            factor = 1.0
        self.mobject.set_fill(opacity=self.living_fill_opacity * factor)
        self.mobject.set_stroke(opacity=self.living_stroke_opacity * factor)
