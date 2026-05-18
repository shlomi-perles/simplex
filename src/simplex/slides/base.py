"""BaseSlide -- thin manim-slides ``Slide`` with the Simplex hierarchy API.

Theme and Manim defaults are no longer wired here. The
``simplex.plugin:activate`` ``manim.plugins`` entry-point applies them once
per render process (each deck's ``manim.cfg`` enables it). What stays in
``BaseSlide`` is the slide-hierarchy override:

- ``self.next_slide(name="...")`` -> main slide, named.
- ``self.next_slide()`` -> sub-slide of the previous main; the **first**
  bare call in a scene auto-promotes itself to a main named after the
  class, and emits a ``UserWarning``.
- ``loop=True`` flips the LOOP variant; an explicit ``section_type=`` always
  wins.

The chosen ``SimplexSectionType.value`` round-trips into manim's native
section JSON (``Section(type_=...) -> JSON "type"``), which the reconciler
in ``simplex.render.reconcile`` reads back to build the main/sub tree.
"""

import warnings
from collections.abc import Iterable
from typing import Any

from manim_slides.slide import Slide

from simplex.engine.animations import clear_scene as _clear_scene
from simplex.engine.region import Region
from simplex.engine.section_types import SimplexSectionType


class BaseSlide(Slide):
    """manim-slides ``Scene`` with the Simplex hierarchy + ``clear_scene``."""

    def setup(self) -> None:
        super().setup()
        self.region = Region.full_frame()

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
        if not hasattr(self, "_simplex_current_main"):
            self._simplex_current_main: str | None = None

        resolved_type = self._resolve_section_type(name, section_type, loop)
        if resolved_type.is_main and name is None:
            # Reached only via auto-promotion path; the helper sets name.
            name = type(self).__name__
        if resolved_type.is_main:
            self._simplex_current_main = name

        kwargs.setdefault(
            "direction",
            "vertical" if resolved_type.is_sub else "horizontal",
        )

        super().next_slide(
            name=name or "unnamed",
            section_type=resolved_type.value,
            loop=loop,
            **kwargs,
        )

    def _resolve_section_type(
        self,
        name: str | None,
        section_type: SimplexSectionType | str | None,
        loop: bool,
    ) -> SimplexSectionType:
        if section_type is not None:
            if isinstance(section_type, SimplexSectionType):
                return section_type
            return SimplexSectionType(section_type)
        if name is not None:
            return SimplexSectionType.MAIN_LOOP if loop else SimplexSectionType.MAIN
        if self._simplex_current_main is None:
            cls_name = type(self).__name__
            warnings.warn(
                f"first next_slide() in {cls_name} has no name; "
                f"auto-promoting to a main slide named {cls_name!r}. "
                f"Pass next_slide(name=...) on the first call to silence this.",
                stacklevel=3,
            )
            return SimplexSectionType.MAIN_LOOP if loop else SimplexSectionType.MAIN
        return SimplexSectionType.SUB_LOOP if loop else SimplexSectionType.SUB

    def clear_scene(self, *, exclude: Iterable[Any] = ()) -> None:
        """Play the registered exit animation for every mobject not in ``exclude``."""
        _clear_scene(self, exclude=exclude)
