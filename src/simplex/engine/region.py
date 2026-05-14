"""Region -- mutable rectangular sub-area of the frame."""

from typing import Literal, Self

import numpy as np
from manim import Mobject
from pydantic import BaseModel, ConfigDict

Anchor = Literal[
    "center",
    "top",
    "bottom",
    "left",
    "right",
    "top-left",
    "top-right",
    "bottom-left",
    "bottom-right",
]


class Region(BaseModel):
    """A mutable axis-aligned region in Manim frame coordinates."""

    model_config = ConfigDict(arbitrary_types_allowed=True)
    top: float
    bottom: float
    left: float
    right: float

    @classmethod
    def full_frame(cls) -> Self:
        from manim import config

        half_w = config.frame_width / 2
        half_h = config.frame_height / 2
        return cls(top=half_h, bottom=-half_h, left=-half_w, right=half_w)

    @property
    def width(self) -> float:
        return self.right - self.left

    @property
    def height(self) -> float:
        return self.top - self.bottom

    @property
    def center(self) -> np.ndarray:
        cx = (self.left + self.right) / 2
        cy = (self.top + self.bottom) / 2
        return np.array([cx, cy, 0.0])

    def _anchor_point(self, anchor: Anchor) -> np.ndarray:
        cx, cy, _ = self.center
        match anchor:
            case "center":
                return np.array([cx, cy, 0.0])
            case "top":
                return np.array([cx, self.top, 0.0])
            case "bottom":
                return np.array([cx, self.bottom, 0.0])
            case "left":
                return np.array([self.left, cy, 0.0])
            case "right":
                return np.array([self.right, cy, 0.0])
            case "top-left":
                return np.array([self.left, self.top, 0.0])
            case "top-right":
                return np.array([self.right, self.top, 0.0])
            case "bottom-left":
                return np.array([self.left, self.bottom, 0.0])
            case "bottom-right":
                return np.array([self.right, self.bottom, 0.0])

    def place(self, mob: Mobject, anchor: Anchor = "center", buff: float = 0.0) -> Mobject:
        """Move `mob` so its anchor sits at the matching point of this region."""
        target = self._anchor_point(anchor)
        mob.move_to(target)
        w, h = mob.width / 2, mob.height / 2
        dx, dy = 0.0, 0.0
        match anchor:
            case "top":
                dy = -(buff + h)
            case "bottom":
                dy = buff + h
            case "left":
                dx = buff + w
            case "right":
                dx = -(buff + w)
            case "top-left":
                dx, dy = buff + w, -(buff + h)
            case "top-right":
                dx, dy = -(buff + w), -(buff + h)
            case "bottom-left":
                dx, dy = buff + w, buff + h
            case "bottom-right":
                dx, dy = -(buff + w), buff + h
            case _:
                pass
        if dx or dy:
            mob.shift(np.array([dx, dy, 0.0]))
        return mob

    def update(
        self,
        *,
        top: float | None = None,
        bottom: float | None = None,
        left: float | None = None,
        right: float | None = None,
    ) -> None:
        if top is not None:
            self.top = top
        if bottom is not None:
            self.bottom = bottom
        if left is not None:
            self.left = left
        if right is not None:
            self.right = right

    def shrink(
        self,
        *,
        top: float = 0.0,
        bottom: float = 0.0,
        left: float = 0.0,
        right: float = 0.0,
    ) -> None:
        self.top -= top
        self.bottom += bottom
        self.left += left
        self.right -= right

    def reset(self) -> None:
        full = Region.full_frame()
        self.top = full.top
        self.bottom = full.bottom
        self.left = full.left
        self.right = full.right
