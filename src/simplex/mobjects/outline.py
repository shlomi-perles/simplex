"""Outline progress mobjects.

``OutlineProgressBar`` is intentionally a vanilla Manim mobject: it does not
know about scenes, slides, or deck metadata. The important layout rule is that
dot centers are supplied explicitly, with :meth:`from_region` deriving those
centers from :meth:`simplex.engine.region.Region.linspace`.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import numpy as np
from manim import RIGHT, AnimationGroup, Create, Dot, FadeIn, LaggedStart, Line, VGroup

from simplex.engine.region import Region
from simplex.theme.context import get_active_theme


class OutlineProgressBar(VGroup):
    """A dot progress bar for outline slides.

    Use :meth:`from_region` when constructing from a Simplex ``Region``. Its
    default path calls ``region.linspace(RIGHT, parts_count)`` with no inset and
    no edge inclusion, so the left margin, inter-dot gaps, and right margin are
    equal exactly as ``Region.linspace`` defines them.
    """

    def __init__(
        self,
        points: Sequence[np.ndarray],
        *,
        dot_radius: float = 0.08,
        moving_dot_scale: float = 2.5,
        line_stroke_width: float = 10.0,
        dot_color: str | None = None,
        accent_color: str | None = None,
        track_color: str | None = None,
        track_opacity: float = 0.35,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        if len(points) < 1:
            raise ValueError("OutlineProgressBar needs at least one point")

        theme = get_active_theme()
        self.dot_points = [np.array(point, dtype=float) for point in points]
        self.dot_color = dot_color or theme.palette.vertex
        self.accent_color = accent_color or theme.palette.accent
        self.track_color = track_color or theme.palette.edge

        self.dots = VGroup(
            *(
                Dot(point=point, radius=dot_radius, color=self.dot_color, z_index=3)
                for point in self.dot_points
            )
        )
        self.dots[0].set_color(self.accent_color)
        self.dots[-1].set_color(self.accent_color)

        self.active_index = 0
        self.moving_dot = Dot(
            point=self.dot_points[0],
            radius=dot_radius * moving_dot_scale,
            color=self.accent_color,
            z_index=4,
        )

        track_end = self.dot_points[-1]
        opacity = track_opacity
        if len(self.dot_points) == 1:
            track_end = self.dot_points[0] + RIGHT * 1e-6
            opacity = 0.0
        self.track = Line(
            self.dot_points[0],
            track_end,
            stroke_width=line_stroke_width,
            color=self.track_color,
            z_index=0,
        ).set_opacity(opacity)
        self.completed_track = Line(
            self.dot_points[0],
            self.dot_points[0] + RIGHT * 1e-6,
            stroke_width=line_stroke_width,
            color=self.accent_color,
            z_index=2,
        )
        self.completed_track.set_opacity(0.0)

        self.add(self.track, self.completed_track, self.dots, self.moving_dot)

    @classmethod
    def from_region(
        cls,
        region: Region,
        parts_count: int,
        *,
        y: float | None = None,
        **kwargs: Any,
    ) -> OutlineProgressBar:
        """Create a horizontal bar whose dots use ``region.linspace`` defaults."""
        points = region.linspace(RIGHT, parts_count, orthogonal=y)
        return cls(points, **kwargs)

    @property
    def spacing(self) -> float:
        """Distance between neighbouring dot centers, or ``0`` for a single dot."""
        if len(self.dot_points) < 2:
            return 0.0
        return float(np.linalg.norm(self.dot_points[1] - self.dot_points[0]))

    def point_at(self, index: int) -> np.ndarray:
        """Return the current center of dot ``index``."""
        self._validate_index(index)
        return self.dots[index].get_center()

    def set_index(self, index: int) -> OutlineProgressBar:
        """Synchronously move the active marker to dot ``index``."""
        self._validate_index(index)
        self.active_index = index
        target = self.dots[index].get_center()
        self.moving_dot.move_to(target)
        line_end = self.dot_points[0] + RIGHT * 1e-6 if index == 0 else target
        self.completed_track.put_start_and_end_on(self.dot_points[0], line_end)
        self.completed_track.set_opacity(0.0 if index == 0 else 1.0)
        return self

    def appear(self, **kwargs: Any) -> AnimationGroup:
        """Default entrance animation for the full bar."""
        return AnimationGroup(
            Create(self.track),
            Create(self.completed_track),
            LaggedStart(*(FadeIn(dot) for dot in self.dots), lag_ratio=0.08),
            FadeIn(self.moving_dot),
            **kwargs,
        )

    def _validate_index(self, index: int) -> None:
        if not 0 <= index < len(self.dot_points):
            raise IndexError(f"dot index {index} out of range for {len(self.dot_points)} dots")
