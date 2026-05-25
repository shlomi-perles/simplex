"""Reusable outline slide scene.

The public contract is deliberately small: authors provide fully constructed
Manim mobjects in :class:`OutlinePart`; the scene handles the outline
choreography and progress geometry.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any, cast

import numpy as np
from manim import (
    RIGHT,
    UP,
    Animation,
    AnimationGroup,
    DrawBorderThenFill,
    FadeIn,
    FadeOut,
    Group,
    Mobject,
    MoveToTarget,
    ReplacementTransform,
    TransformMatchingShapes,
    VGroup,
    VMobject,
    Write,
)

from simplex.engine.region import Region
from simplex.engine.scaling import scale_to_fit
from simplex.mobjects.outline import OutlineProgressBar
from simplex.section import SimplexSectionType
from simplex.slides.base import BaseSlide
from simplex.theme.context import get_active_theme

type VisualAnimation = Animation | Callable[[Mobject], Animation]

_DEFAULT_PROGRESS_Y_FRACTION = 0.2
_CONTENT_BUFF = 0.35
_LABEL_BUFF = 0.2
_THUMBNAIL_BUFF = 0.15
_LABEL_WIDTH_FRACTION = 0.9
_THUMBNAIL_WIDTH_FRACTION = 0.3


@dataclass(slots=True)
class OutlinePart:
    """One semantic stop in an outline scene.

    Args:
        title: Large feature mobject shown while this part is active.
        label: Compact mobject left below the progress dot after the part
            collapses.
        visual: Optional feature visual, later collapsed above the progress dot.
        visual_animation: Optional extra animation played after the visual is
            introduced. Pass a callable when the animation should be built from
            the visual's final feature placement.
        feature_visual_scale: Multiplier for the large visual fit box.
        thumbnail_scale: Multiplier for the collapsed visual width.
    """

    title: Mobject
    label: Mobject
    visual: Mobject | None = None
    visual_animation: VisualAnimation | None = None
    feature_visual_scale: float = 1.0
    thumbnail_scale: float = 1.0


class OutlineScene(BaseSlide):
    """Animated lecture outline built from :class:`OutlinePart` objects.

    Progress dots are positioned through ``self.region.linspace(RIGHT, n)`` by
    :class:`OutlineProgressBar`; only the orthogonal y-coordinate is overridden
    so the x-axis geometry remains the default Simplex ``linspace`` layout.

    ``start_index`` and ``end_index`` define the sequential slice to animate;
    parts before ``start_index`` are prepared as already-collapsed context.
    ``focus_index`` instead reveals the compact outline and expands one target
    part, which is useful for per-section recap slides.
    """

    def __init__(
        self,
        parts: Sequence[OutlinePart],
        *,
        start_index: int = 0,
        end_index: int | None = None,
        focus_index: int | None = None,
        progress_y: float = _DEFAULT_PROGRESS_Y_FRACTION,
        section_name: str = "Outline",
        progress_run_time: float = 1.0,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.parts = list(parts)
        self.part_count = len(self.parts)
        if self.part_count == 0:
            raise ValueError("OutlineScene needs at least one part")

        self.start_index = start_index
        self.end_index = self.part_count if end_index is None else end_index
        self.focus_index = focus_index
        self.progress_y = progress_y
        self.section_name = section_name
        self.progress_run_time = progress_run_time
        self.current_index = 0
        self.outline_started = False

        self._validate_indices()

        self.progress_bar: OutlineProgressBar
        self.dots: VGroup
        self.compact_mobjects: Group
        self.initial_mobjects: Group
        self._labels_are_fit = False

    def construct(self) -> None:
        self.progress_bar = self.make_progress_bar()
        self._fit_all_labels()
        self.compact_mobjects = Group()
        self.initial_mobjects = Group(self.progress_bar)

        self.next_slide(name=self.section_name)

        if self.focus_index is not None:
            self._run_focused_outline(self.focus_index)
            return

        for index in range(self.start_index):
            self._prepare_compact_part(index)
        for index in range(self.start_index, self.end_index):
            self.play_part(index)

        self.fade_outline()

    def make_progress_bar(self) -> OutlineProgressBar:
        """Create the progress bar with ``Region.linspace`` dot centers."""
        bar = OutlineProgressBar.from_region(
            self.region,
            self.part_count,
            y=self._progress_bar_y(),
        )
        self.dots = bar.dots
        return bar

    def play_part(self, index: int) -> None:
        """Play one outline stop."""
        self._validate_part_index(index)
        if not self.outline_started:
            self.reveal_outline()

        part = self.parts[index]
        self.play(self._animate_progress(index))
        self.wait(0.1)

        self._place_title(part)
        self.play(self._enter(part.title))
        if part.visual is not None:
            self._show_feature_visual(part)

        self._collapse_part(index, part)
        self.current_index = index + 1

    def reveal_outline(self) -> None:
        """Reveal the progress bar and any pre-built compact context."""
        self.outline_started = True
        intro: list[Any] = [self.progress_bar.appear()]
        intro.extend(FadeIn(mob) for mob in self.initial_mobjects.submobjects[1:])
        self.play(AnimationGroup(*intro, lag_ratio=0.04))

    def fade_outline(self, *extra: Mobject) -> None:
        """Fade out the outline and optional feature mobjects."""
        if not self.outline_started:
            return
        self.next_slide(name="End Outline", section_type=SimplexSectionType.SUB)
        targets = self._unique_mobjects(
            [self.progress_bar, *self.compact_mobjects.submobjects, *extra]
        )
        self.play(*(FadeOut(mob) for mob in targets))

    def _run_focused_outline(self, focus_index: int) -> None:
        self._validate_part_index(focus_index)
        self.progress_bar.set_index(max(0, focus_index - 1))
        for index in range(self.part_count):
            self._prepare_compact_part(index)

        self.reveal_outline()

        part = self.parts[focus_index]
        self._place_title(part)
        animations: list[Any] = [
            self._enter(part.title),
            self._animate_progress(focus_index),
        ]
        if part.visual is not None:
            part.visual.generate_target()
            target = cast(Mobject, cast(Any, part.visual).target)
            self._place_feature_visual(target, part, exclude_compact=part.visual)
            animations.append(MoveToTarget(part.visual))
        self.play(*animations)
        self.fade_outline(part.title)

    def _collapse_part(self, index: int, part: OutlinePart) -> None:
        self.next_slide()

        self._place_label(index, part.label)
        animations: list[Any] = [self._title_to_label_animation(part.title, part.label)]

        if part.visual is not None:
            part.visual.generate_target()
            target = cast(Mobject, cast(Any, part.visual).target)
            self._place_thumbnail(index, target, part.thumbnail_scale)
            animations.append(MoveToTarget(part.visual))

        self.play(*animations)
        self.remove(part.title)
        self.add(part.label)
        self._remember_compact(part.label)
        if part.visual is not None:
            self._remember_compact(part.visual)

    def _show_feature_visual(self, part: OutlinePart) -> None:
        if part.visual is None:
            return
        self._place_feature_visual(part.visual, part)
        if isinstance(part.visual, VMobject):
            self.play(DrawBorderThenFill(part.visual))
        else:
            self.play(FadeIn(part.visual))

        animation = part.visual_animation
        if animation is None:
            return
        self.next_slide()
        self.play(animation(part.visual) if callable(animation) else animation)
        self.wait(0.001)

    def _prepare_compact_part(self, index: int) -> None:
        part = self.parts[index]
        self._place_label(index, part.label)
        self._remember_initial(part.label)
        self._remember_compact(part.label)
        if part.visual is not None:
            self._place_thumbnail(index, part.visual, part.thumbnail_scale)
            self._remember_initial(part.visual)
            self._remember_compact(part.visual)

    def _place_title(self, part: OutlinePart) -> None:
        self._set_font_size(part.title, get_active_theme().typography.h1)
        scale_to_fit(part.title, len_x=self.region.width * 0.9, max_scale=1.0)
        if part.visual is not None:
            part.title.to_edge(UP)
            return
        title_region = Region(
            top=self.region.top,
            bottom=self.dots,
            left=self.region.left,
            right=self.region.right,
        )
        title_region.place(part.title)

    def _place_feature_visual(
        self,
        visual: Mobject,
        part: OutlinePart,
        *,
        exclude_compact: Mobject | None = None,
    ) -> None:
        feature_region = self._feature_region(part, exclude_compact=exclude_compact)
        scale_to_fit(
            visual,
            len_x=feature_region.width,
            len_y=feature_region.height,
            scaleback=part.feature_visual_scale,
        )
        feature_region.place(visual)

    def _place_label(self, index: int, label: Mobject) -> None:
        self._fit_all_labels()
        label.move_to(self._label_point(index))

    def _place_thumbnail(self, index: int, visual: Mobject, scale: float) -> None:
        thumbnail_extent = self._progress_spacing() * _THUMBNAIL_WIDTH_FRACTION * scale
        scale_to_fit(
            visual,
            len_x=thumbnail_extent,
            len_y=thumbnail_extent,
        )
        visual.next_to(self.dots[index], UP, buff=_THUMBNAIL_BUFF)

    def _progress_bar_y(self) -> float:
        if self.progress_y < 0:
            raise ValueError("progress_y must be non-negative")
        if self.progress_y <= 1.0:
            return self.region.bottom + self.region.height * self.progress_y
        return self.region.bottom + self.progress_y

    def _feature_region(
        self,
        part: OutlinePart,
        *,
        exclude_compact: Mobject | None = None,
    ) -> Region:
        feature_region = Region(
            top=part.title,
            bottom=self._feature_bottom(exclude_compact=exclude_compact),
            left=self.region.left,
            right=self.region.right,
        )
        feature_region.shrink(top=_CONTENT_BUFF, bottom=_CONTENT_BUFF)
        if feature_region.top <= feature_region.bottom:
            feature_region.update(bottom=self.progress_bar)
            feature_region.shrink(bottom=_CONTENT_BUFF)
        if feature_region.top <= feature_region.bottom:
            feature_region.bottom = feature_region.top - 1e-6
        return feature_region

    def _feature_bottom(self, *, exclude_compact: Mobject | None = None) -> float:
        bottom = self.progress_bar.get_top()[1]
        for part in self.parts:
            visual = part.visual
            if (
                visual is None
                or visual is exclude_compact
                or visual not in self.compact_mobjects.submobjects
            ):
                continue
            bottom = max(bottom, float(visual.get_top()[1]))
        return bottom

    def _label_region(self) -> Region:
        label_region = Region(
            top=self.progress_bar,
            bottom=self.region.bottom,
            left=self.region.left,
            right=self.region.right,
        )
        if label_region.top <= self.region.bottom:
            label_region.top = self.region.bottom + 1e-6
        return label_region

    def _label_point(self, index: int) -> np.ndarray:
        return self._label_region().linspace(RIGHT, self.part_count)[index]

    def _fit_all_labels(self) -> None:
        if self._labels_are_fit:
            return

        label_region = self._label_region()
        for part in self.parts:
            scale_to_fit(
                part.label,
                len_x=self._progress_spacing() * _LABEL_WIDTH_FRACTION,
                len_y=label_region.height,
                buff=_LABEL_BUFF,
            )

        font_sizes = [
            float(font_mobject.font_size)
            for part in self.parts
            for font_mobject in self._font_mobjects(part.label)
        ]
        if font_sizes:
            font_size = min(font_sizes)
            for part in self.parts:
                for font_mobject in self._font_mobjects(part.label):
                    font_mobject.font_size = font_size

        self._labels_are_fit = True

    def _progress_spacing(self) -> float:
        if self.progress_bar.spacing > 0:
            return self.progress_bar.spacing
        return self.region.width

    def _enter(self, mob: Mobject) -> Any:
        return Write(mob) if isinstance(mob, VMobject) else FadeIn(mob)

    def _animate_progress(self, index: int) -> Any:
        builder = cast(Any, self.progress_bar.animate)
        return builder(run_time=self.progress_run_time).set_index(index)

    def _title_to_label_animation(self, title: Mobject, label: Mobject) -> Animation:
        if isinstance(title, VMobject) and isinstance(label, VMobject):
            return TransformMatchingShapes(title, label)
        return ReplacementTransform(title, label)

    def _remember_initial(self, mob: Mobject) -> None:
        if mob not in self.initial_mobjects.submobjects:
            self.initial_mobjects.add(mob)

    def _remember_compact(self, mob: Mobject) -> None:
        if mob not in self.compact_mobjects.submobjects:
            self.compact_mobjects.add(mob)

    def _validate_indices(self) -> None:
        if not 0 <= self.start_index <= self.end_index <= self.part_count:
            raise ValueError(
                "start_index and end_index must define a valid Python-style slice; "
                f"got start_index={self.start_index}, end_index={self.end_index}, "
                f"part_count={self.part_count}"
            )
        if self.focus_index is not None:
            self._validate_part_index(self.focus_index)

    def _validate_part_index(self, index: int) -> None:
        if not 0 <= index < self.part_count:
            raise IndexError(f"part index {index} out of range for {self.part_count} parts")

    @staticmethod
    def _unique_mobjects(mobjects: Sequence[Mobject]) -> list[Mobject]:
        seen: set[int] = set()
        out: list[Mobject] = []
        for mob in mobjects:
            ident = id(mob)
            if ident not in seen:
                out.append(mob)
                seen.add(ident)
        return out

    @staticmethod
    def _font_mobjects(mob: Mobject) -> list[Any]:
        return [cast(Any, submob) for submob in mob.get_family() if hasattr(submob, "font_size")]

    @classmethod
    def _set_font_size(cls, mob: Mobject, font_size: float) -> None:
        for font_mobject in cls._font_mobjects(mob):
            font_mobject.font_size = font_size
