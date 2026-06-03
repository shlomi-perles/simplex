"""Slide classes built on manim-slides with the Simplex hierarchy API.

Theme and Manim defaults are wired in ``simplex.plugin:activate`` (the
``manim.plugins`` entry-point) once per render process. What stays in
``Slide`` / ``ThreeDSlide`` is the slide-hierarchy override:

- ``self.next_slide(name="Title")`` -> **main** slide, named ``"Title"``.
- ``self.next_slide()`` *as the first call* -> auto-promoted to a **main**
  slide named after the scene class with spaces inserted between
  PascalCase boundaries (``DFSLecture -> "DFS Lecture"``,
  ``ImplementBFSSlide -> "Implement BFS Slide"``).
- ``self.next_slide()`` *after a named main* -> **sub** of that main.
- ``loop=True`` flips to the ``LOOP`` variant; an explicit ``section_type=``
  always wins.
- ``wait_time_between_slides`` defaults to a small final-frame hold so the
  encoded slide segment includes the completed state of the last animation.
- reverse-video generation is skipped; Simplex's web/PDF/PPTX pipeline consumes
  the forward slide media and Manim's native section videos.

The chosen ``SimplexSectionType.value`` round-trips into Manim's native
section JSON (``Section(type_=...) -> JSON "type"``), which the reconciler
in ``simplex.render.reconcile`` reads back to build the main/sub tree.
"""

import os
import re
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any, cast

from manim_slides.slide import Slide as ManimSlide
from manim_slides.slide import ThreeDSlide as ManimThreeDSlide

from simplex.engine.animations import clear_scene as _clear_scene
from simplex.engine.region import Region
from simplex.section import SimplexSectionType
from simplex.slides.chrome import Chrome, ChromeContent, make_chrome
from simplex.theme.context import get_active_theme

# Insert a space between a run of capitals and a Title-cased word
# (``BFSLecture`` -> ``BFS Lecture``) and between any lower/Upper pair
# (``ImplementBFS`` -> ``Implement BFS``).
_CAMEL_TAIL = re.compile(r"([A-Z]+)([A-Z][a-z])")
_CAMEL_LOWER = re.compile(r"([a-z\d])([A-Z])")
DEFAULT_SLIDE_BOUNDARY_WAIT_TIME = 0.1


def _simplex_slides_output_folder() -> Path | None:
    raw = os.environ.get("SIMPLEX_SLIDES_DIR")
    return Path(raw) if raw else None


def _pretty_class_name(name: str) -> str:
    """Split a PascalCase class name into human-readable words.

    Examples:
        ``DFSLecture``       -> ``"DFS Lecture"``
        ``ImplementBFSSlide`` -> ``"Implement BFS Slide"``
        ``Title``            -> ``"Title"``
    """
    spaced = _CAMEL_TAIL.sub(r"\1 \2", name)
    return _CAMEL_LOWER.sub(r"\1 \2", spaced)


class _SimplexSlideMixin:
    """Simplex behavior shared by 2D and 3D manim-slides scenes."""

    header: ChromeContent = None
    footer: ChromeContent = None
    chrome_kwargs: Mapping[str, Any] = {}
    skip_reversing = True
    slide_boundary_wait_time: float = DEFAULT_SLIDE_BOUNDARY_WAIT_TIME
    _current_main: str | None

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        output_folder = _simplex_slides_output_folder()
        if output_folder is not None:
            kwargs.setdefault("output_folder", output_folder)
        cast(Any, super()).__init__(*args, **kwargs)

    def setup(self) -> None:
        cast(Any, super()).setup()
        cast(Any, self).wait_time_between_slides = self.slide_boundary_wait_time
        self.region = Region.full_frame()
        self._current_main = None
        self.setup_chrome()

    def setup_chrome(self, **kwargs: Any) -> Chrome | None:
        """Add header/footer chrome to the scene canvas and shrink ``self.region``.

        Defaults come from ``self.header``, ``self.footer`` and
        ``self.chrome_kwargs``. A call with no header and no footer is a no-op,
        which keeps plain slides lightweight.
        """
        chrome_kwargs = dict(self.chrome_kwargs)
        chrome_kwargs.update(kwargs)
        chrome_kwargs.setdefault("header", self.header)
        chrome_kwargs.setdefault("footer", self.footer)
        if chrome_kwargs["header"] is None and chrome_kwargs["footer"] is None:
            return None

        theme = chrome_kwargs.pop("theme", get_active_theme())
        region = chrome_kwargs.pop("region", self.region)
        chrome = make_chrome(theme, region, **chrome_kwargs)
        cast(Any, self).add_to_canvas(**chrome.mobjects)
        if chrome.mobjects:
            cast(Any, self).add(*chrome.mobjects.values())
            add_fixed = getattr(self, "add_fixed_in_frame_mobjects", None)
            if callable(add_fixed):
                add_fixed(*chrome.mobjects.values())
        self.region = chrome.body_region
        return chrome

    def next_slide(
        self,
        name: str | None = None,
        *,
        section_type: SimplexSectionType | str | None = None,
        loop: bool = False,
        **kwargs: Any,
    ) -> None:
        """Hierarchical next_slide.

        See module docstring for the rules; this method just forwards to
        ``manim_slides.Slide.next_slide`` with the resolved ``section_type``
        and a sensible default for RevealJS ``direction``.
        """
        resolved = self._resolve_section_type(name, section_type, loop)

        if resolved.is_main:
            # If the caller didn't name it (bare first call, or explicit MAIN
            # section_type with no name), fall back to the class name with
            # spaces between PascalCase boundaries.
            if name is None:
                name = _pretty_class_name(type(self).__name__)
            self._current_main = name

        kwargs.setdefault(
            "direction",
            "vertical" if resolved.is_sub else "horizontal",
        )

        wait_time = self._pad_current_slide()
        if wait_time > 0.0:
            cast(Any, self).wait_time_between_slides = 0.0
        try:
            cast(Any, super()).next_slide(
                name=name or self._current_main or "unnamed",
                section_type=resolved.value,
                loop=loop,
                **kwargs,
            )
        finally:
            if wait_time > 0.0:
                cast(Any, self).wait_time_between_slides = wait_time

    def _pad_current_slide(self) -> float:
        """Hold the final frame before closing Simplex's native Manim section."""
        wait_time = float(cast(Any, self).wait_time_between_slides)
        if wait_time <= 0.0:
            return wait_time

        current_animation = int(getattr(self, "_current_animation", 0))
        start_animation = int(getattr(self, "_start_animation", 0))
        if current_animation > start_animation:
            cast(Any, self).wait(wait_time)
        return wait_time

    def _resolve_section_type(
        self,
        name: str | None,
        section_type: SimplexSectionType | str | None,
        loop: bool,
    ) -> SimplexSectionType:
        # Explicit section_type always wins.
        if section_type is not None:
            if isinstance(section_type, SimplexSectionType):
                return section_type
            return SimplexSectionType(section_type)
        # Named call -> MAIN (LOOP variant on loop=True).
        if name is not None:
            return SimplexSectionType.MAIN_LOOP if loop else SimplexSectionType.MAIN
        # Bare call: if no main has been opened yet, auto-promote to MAIN
        # named after the class. After the first main, bare = SUB.
        if self._current_main is None:
            return SimplexSectionType.MAIN_LOOP if loop else SimplexSectionType.MAIN
        return SimplexSectionType.SUB_LOOP if loop else SimplexSectionType.SUB

    def clear_scene(self, *, exclude: Iterable[Any] = ()) -> None:
        """Play the registered exit animation for every mobject not in ``exclude``."""
        _clear_scene(self, exclude=exclude)


class Slide(_SimplexSlideMixin, ManimSlide):
    """``manim_slides.Slide`` with Simplex hierarchy, regions, and chrome."""


class ThreeDSlide(_SimplexSlideMixin, ManimThreeDSlide):
    """``manim_slides.ThreeDSlide`` with Simplex hierarchy, regions, and chrome."""


BaseSlide = Slide
