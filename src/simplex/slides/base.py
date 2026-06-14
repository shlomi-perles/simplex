"""Simplex-owned Manim scene classes for timeline-native playback."""

from __future__ import annotations

import os
import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from manim import Scene, ThreeDScene
from manim import config as manim_config

from simplex.engine.animations import clear_scene as _clear_scene
from simplex.engine.defaults import apply_theme_defaults
from simplex.engine.region import Region
from simplex.manifest import SceneCue, SceneCueManifest
from simplex.section import CueKind, SimplexSectionType
from simplex.slides.chrome import Chrome, ChromeContent, make_chrome
from simplex.theme.context import get_active_theme, set_default_theme

_CAMEL_TAIL = re.compile(r"([A-Z]+)([A-Z][a-z])")
_CAMEL_LOWER = re.compile(r"([a-z\d])([A-Z])")
_SLUG_CLEAN = re.compile(r"[^a-z0-9]+")
DEFAULT_CUE_BOUNDARY_WAIT_TIME = 0.1


def _pretty_class_name(name: str) -> str:
    spaced = _CAMEL_TAIL.sub(r"\1 \2", name)
    return _CAMEL_LOWER.sub(r"\1 \2", spaced)


def _slugify(value: str) -> str:
    slug = _SLUG_CLEAN.sub("-", value.lower()).strip("-")
    return slug or "cue"


def _cue_output_dir() -> Path | None:
    raw = os.environ.get("SIMPLEX_CUES_DIR")
    return Path(raw) if raw else None


def _scene_unit(scene: Any) -> str:
    return os.environ.get("SIMPLEX_SCENE_UNIT") or (
        f"{type(scene).__module__}:{type(scene).__name__}"
    )


@dataclass(slots=True)
class _OpenCue:
    id: str
    auto_id: bool
    kind: CueKind
    title: str
    unit: str
    start: float
    start_frame: int
    notes: str | None


class _SimplexSceneMixin:
    """Shared cue recording, chrome, and region helpers."""

    header: ChromeContent = None
    footer: ChromeContent = None
    chrome_kwargs: Mapping[str, Any] = {}
    cue_boundary_wait_time: float = DEFAULT_CUE_BOUNDARY_WAIT_TIME

    region: Region
    _simplex_cues: list[SceneCue]
    _simplex_current: _OpenCue | None
    _simplex_auto_counts: dict[CueKind, int]
    _simplex_current_main_id: str | None
    _simplex_current_main_cue_number: int
    _simplex_canvas: dict[str, Any]

    def setup(self) -> None:
        cast(Any, super()).setup()
        self._apply_scene_theme()
        self.region = Region.full_frame()
        self._simplex_cues = []
        self._simplex_current = None
        self._simplex_auto_counts = {}
        self._simplex_current_main_id = None
        self._simplex_current_main_cue_number = 0
        self._simplex_canvas = {}
        self.setup_chrome()

    def tear_down(self) -> None:
        self._close_current_cue(pad=True)
        self._write_simplex_cues()
        cast(Any, super()).tear_down()

    def add_to_canvas(self, **mobjects: Any) -> None:
        """Store named chrome mobjects for callers that want to inspect them."""
        self._simplex_canvas.update(mobjects)

    @property
    def canvas(self) -> Mapping[str, Any]:
        return self._simplex_canvas

    def _apply_scene_theme(self) -> None:
        """Apply active theme defaults to this already-constructed Scene."""
        theme = get_active_theme()
        set_default_theme(theme)
        apply_theme_defaults(theme)
        manim_config.tex_template = theme.latex.as_tex_template()
        manim_config.background_color = theme.palette.background
        camera = getattr(self, "camera", None)
        if camera is not None and hasattr(camera, "background_color"):
            camera.background_color = theme.palette.background
        renderer = getattr(self, "renderer", None)
        if renderer is not None and hasattr(renderer, "background_color"):
            renderer.background_color = theme.palette.background

    def setup_chrome(self, **kwargs: Any) -> Chrome | None:
        """Add header/footer chrome and shrink ``self.region`` around it."""
        chrome_kwargs = dict(self.chrome_kwargs)
        chrome_kwargs.update(kwargs)
        chrome_kwargs.setdefault("header", self.header)
        chrome_kwargs.setdefault("footer", self.footer)
        if chrome_kwargs["header"] is None and chrome_kwargs["footer"] is None:
            return None

        theme = chrome_kwargs.pop("theme", get_active_theme())
        region = chrome_kwargs.pop("region", self.region)
        chrome = make_chrome(theme, region, **chrome_kwargs)
        self.add_to_canvas(**chrome.mobjects)
        if chrome.mobjects:
            cast(Any, self).add(*chrome.mobjects.values())
            add_fixed = getattr(self, "add_fixed_in_frame_mobjects", None)
            if callable(add_fixed):
                add_fixed(*chrome.mobjects.values())
        self.region = chrome.body_region
        return chrome

    def slide(
        self,
        cue_id: str | None = None,
        *,
        title: str | None = None,
        notes: str | None = None,
    ) -> None:
        """Mark a primary slide boundary in the current scene unit."""
        self._open_cue(CueKind.SLIDE, cue_id, title=title, notes=notes)

    def fragment(
        self,
        cue_id: str | None = None,
        *,
        title: str | None = None,
        notes: str | None = None,
    ) -> None:
        """Mark a sub-stop within the current slide."""
        self._open_cue(CueKind.FRAGMENT, cue_id, title=title, notes=notes)

    def loop(
        self,
        cue_id: str | None = None,
        *,
        title: str | None = None,
        notes: str | None = None,
    ) -> None:
        """Mark a cue that loops in presentation mode."""
        self._open_cue(CueKind.LOOP, cue_id, title=title, notes=notes)

    def skip(
        self,
        cue_id: str | None = None,
        *,
        title: str | None = None,
        notes: str | None = None,
    ) -> None:
        """Mark a cue that exports can skip while playback can still address it."""
        self._open_cue(CueKind.SKIP, cue_id, title=title, notes=notes)

    def next_slide(
        self,
        name: str | None = None,
        *,
        section_type: SimplexSectionType | str | None = None,
        loop: bool = False,
        **_kwargs: Any,
    ) -> None:
        """Thin transitional alias for local examples that still call ``next_slide``.

        The method records Simplex cues only; it never calls Manim
        ``next_section`` or manim-slides.
        """
        kind = self._kind_from_legacy_next_slide(name, section_type, loop)
        if self._should_backfill_first_legacy_marker():
            self._open_cue(kind, None, title=name, notes=None, start=0.0)
            self._close_current_cue(pad=True)
            self._open_cue(CueKind.FRAGMENT, None, title=None, notes=None)
            return
        marker = {
            CueKind.SLIDE: self.slide,
            CueKind.FRAGMENT: self.fragment,
            CueKind.LOOP: self.loop,
            CueKind.SKIP: self.skip,
        }[kind]
        marker(title=name)

    def clear_scene(self, *, exclude: Iterable[Any] = ()) -> None:
        _clear_scene(self, exclude=exclude)

    def _open_cue(
        self,
        kind: CueKind,
        cue_id: str | None,
        *,
        title: str | None,
        notes: str | None,
        start: float | None = None,
    ) -> None:
        self._close_current_cue(pad=True)
        resolved_title = title or self._default_title(kind)
        auto = cue_id is None or not cue_id.strip()
        if auto:
            candidate_id = self._auto_cue_id(kind, resolved_title)
        else:
            assert cue_id is not None
            candidate_id = cue_id.strip()
        resolved_id = self._dedupe_cue_id(candidate_id)
        if kind.is_slide:
            self._simplex_current_main_id = resolved_id
            self._simplex_current_main_cue_number = 1
        start_time = float(cast(Any, self).time) if start is None else float(start)
        self._simplex_current = _OpenCue(
            id=resolved_id,
            auto_id=auto,
            kind=kind,
            title=resolved_title,
            unit=_scene_unit(self),
            start=start_time,
            start_frame=self._frame_number(start_time),
            notes=notes,
        )

    def _close_current_cue(self, *, pad: bool) -> None:
        current = self._simplex_current
        if current is None:
            return
        if pad and self._should_pad_current_cue(current):
            cast(Any, self).wait(float(self.cue_boundary_wait_time))
        end = float(cast(Any, self).time)
        end_frame = self._frame_number(end)
        if end_frame < current.start_frame:
            end_frame = current.start_frame
        if end < current.start:
            end = current.start
        if end_frame == current.start_frame and end <= current.start + 1e-6:
            self._simplex_current = None
            return
        self._simplex_cues.append(
            SceneCue(
                id=current.id,
                kind=current.kind,
                title=current.title,
                unit=current.unit,
                start_frame=current.start_frame,
                end_frame=end_frame,
                start=current.start,
                end=end,
                notes=current.notes,
                auto_id=current.auto_id,
            )
        )
        self._simplex_current = None

    def _should_backfill_first_legacy_marker(self) -> bool:
        """Treat first post-animation ``next_slide`` as the end of slide one."""
        if self._simplex_cues or self._simplex_current is not None:
            return False
        return float(cast(Any, self).time) > 1e-6

    def _should_pad_current_cue(self, current: _OpenCue) -> bool:
        wait_time = float(self.cue_boundary_wait_time)
        if wait_time <= 0.0:
            return False
        if float(cast(Any, self).time) <= current.start + 1e-6:
            return False
        renderer = getattr(self, "renderer", None)
        num_plays = getattr(renderer, "num_plays", None)
        if not isinstance(num_plays, int):
            return True
        try:
            upto_animation_number = float(manim_config.upto_animation_number)
        except (TypeError, ValueError):
            return True
        return num_plays <= upto_animation_number

    def _write_simplex_cues(self) -> None:
        out_dir = _cue_output_dir()
        if out_dir is None:
            return
        scene_name = type(self).__name__
        duration = float(cast(Any, self).time)
        manifest = SceneCueManifest(
            scene=scene_name,
            unit=_scene_unit(self),
            fps=round(float(manim_config.frame_rate)),
            duration=duration,
            duration_frames=self._frame_number(duration),
            cues=tuple(self._simplex_cues or (self._implicit_cue(duration),)),
        )
        manifest.write(out_dir / f"{scene_name}.json")

    def _implicit_cue(self, duration: float) -> SceneCue:
        title = _pretty_class_name(type(self).__name__)
        return SceneCue(
            id=_slugify(title),
            kind=CueKind.SLIDE,
            title=title,
            unit=_scene_unit(self),
            start_frame=0,
            end_frame=self._frame_number(duration),
            start=0.0,
            end=duration,
            auto_id=True,
        )

    def _frame_number(self, seconds: float) -> int:
        fps = float(manim_config.frame_rate)
        return max(0, round(seconds * fps))

    def _default_title(self, kind: CueKind) -> str:
        if kind.is_slide and not self._simplex_cues:
            return _pretty_class_name(type(self).__name__)
        count = self._simplex_auto_counts.get(kind, 0) + 1
        self._simplex_auto_counts[kind] = count
        if kind.is_fragment:
            return f"{_pretty_class_name(type(self).__name__)} Detail {count}"
        return f"{_pretty_class_name(type(self).__name__)} {kind.value.title()} {count}"

    def _auto_cue_id(self, kind: CueKind, title: str) -> str:
        if kind.is_slide:
            return _slugify(title)

        main_id = self._simplex_current_main_id
        if main_id is None:
            main_id = _slugify(_pretty_class_name(type(self).__name__))
            self._simplex_current_main_id = main_id
            self._simplex_current_main_cue_number = 1
        self._simplex_current_main_cue_number += 1
        return f"{main_id}-{self._simplex_current_main_cue_number}"

    def _dedupe_cue_id(self, cue_id: str) -> str:
        existing = {cue.id for cue in self._simplex_cues}
        if self._simplex_current is not None:
            existing.add(self._simplex_current.id)
        if cue_id not in existing:
            return cue_id
        index = 2
        while f"{cue_id}-{index}" in existing:
            index += 1
        return f"{cue_id}-{index}"

    def _kind_from_legacy_next_slide(
        self,
        name: str | None,
        section_type: SimplexSectionType | str | None,
        loop: bool,
    ) -> CueKind:
        if section_type is not None:
            resolved = (
                section_type
                if isinstance(section_type, SimplexSectionType)
                else SimplexSectionType(section_type)
            )
            if resolved.is_skip:
                return CueKind.SKIP
            if resolved.is_loop:
                return CueKind.LOOP
            return CueKind.SLIDE if resolved.is_main else CueKind.FRAGMENT
        if loop:
            return CueKind.LOOP
        if name is not None or (not self._simplex_cues and self._simplex_current is None):
            return CueKind.SLIDE
        return CueKind.FRAGMENT


class SimplexScene(_SimplexSceneMixin, Scene):
    """Base class for timeline-native 2D Simplex scenes."""


class SimplexThreeDScene(_SimplexSceneMixin, ThreeDScene):
    """Base class for timeline-native 3D Simplex scenes."""


Slide = SimplexScene
ThreeDSlide = SimplexThreeDScene
BaseSlide = SimplexScene
