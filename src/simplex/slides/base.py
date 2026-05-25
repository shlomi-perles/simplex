"""BaseSlide -- thin manim-slides ``Slide`` with the Simplex hierarchy API.

Theme and Manim defaults are wired in ``simplex.plugin:activate`` (the
``manim.plugins`` entry-point) once per render process. What stays in
``BaseSlide`` is the slide-hierarchy override:

- ``self.next_slide(name="Title")`` -> **main** slide, named ``"Title"``.
- ``self.next_slide()`` *as the first call* -> auto-promoted to a **main**
  slide named after the scene class with spaces inserted between
  PascalCase boundaries (``DFSLecture -> "DFS Lecture"``,
  ``ImplementBFSSlide -> "Implement BFS Slide"``).
- ``self.next_slide()`` *after a named main* -> **sub** of that main.
- ``loop=True`` flips to the ``LOOP`` variant; an explicit ``section_type=``
  always wins.

The chosen ``SimplexSectionType.value`` round-trips into Manim's native
section JSON (``Section(type_=...) -> JSON "type"``), which the reconciler
in ``simplex.render.reconcile`` reads back to build the main/sub tree.
"""

import re
from collections.abc import Iterable
from typing import Any

from manim_slides.slide import Slide

from simplex.engine.animations import clear_scene as _clear_scene
from simplex.engine.region import Region
from simplex.section import SimplexSectionType

# Insert a space between a run of capitals and a Title-cased word
# (``BFSLecture`` -> ``BFS Lecture``) and between any lower/Upper pair
# (``ImplementBFS`` -> ``Implement BFS``).
_CAMEL_TAIL = re.compile(r"([A-Z]+)([A-Z][a-z])")
_CAMEL_LOWER = re.compile(r"([a-z\d])([A-Z])")


def _pretty_class_name(name: str) -> str:
    """Split a PascalCase class name into human-readable words.

    Examples:
        ``DFSLecture``       -> ``"DFS Lecture"``
        ``ImplementBFSSlide`` -> ``"Implement BFS Slide"``
        ``Title``            -> ``"Title"``
    """
    spaced = _CAMEL_TAIL.sub(r"\1 \2", name)
    return _CAMEL_LOWER.sub(r"\1 \2", spaced)


class BaseSlide(Slide):
    """``manim_slides.Slide`` with the Simplex hierarchy + ``clear_scene``."""

    _current_main: str | None

    def setup(self) -> None:
        super().setup()
        self.region = Region.full_frame()
        self._current_main = None

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

        super().next_slide(
            name=name or self._current_main or "unnamed",
            section_type=resolved.value,
            loop=loop,
            **kwargs,
        )

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
