"""Cue kinds used by the timeline-native Simplex playback stack.

This module is intentionally Manim-free. Scene classes, render packaging,
exports, and the web player all import these string enums without pulling in
Manim or browser-only code.
"""

from enum import StrEnum


class CueKind(StrEnum):
    """Semantic cue types recorded by ``SimplexScene``."""

    SLIDE = "slide"
    FRAGMENT = "fragment"
    LOOP = "loop"
    SKIP = "skip"

    @property
    def is_slide(self) -> bool:
        return self is CueKind.SLIDE

    @property
    def is_fragment(self) -> bool:
        return self is CueKind.FRAGMENT

    @property
    def is_loop(self) -> bool:
        return self is CueKind.LOOP

    @property
    def is_skip(self) -> bool:
        return self is CueKind.SKIP


class SimplexSectionType(StrEnum):
    """Legacy section type names retained for transitional internal imports.

    The timeline renderer does not emit or consume Manim section JSON. Keeping
    this enum lightweight lets older helper tests and any untouched internal
    utilities import successfully while new code uses :class:`CueKind`.
    """

    MAIN = "simplex.main"
    SUB = "simplex.sub"
    MAIN_LOOP = "simplex.main.loop"
    SUB_LOOP = "simplex.sub.loop"
    MAIN_SKIP = "simplex.main.skip"
    SUB_SKIP = "simplex.sub.skip"

    @property
    def is_main(self) -> bool:
        return self.value.startswith("simplex.main")

    @property
    def is_sub(self) -> bool:
        return self.value.startswith("simplex.sub")

    @property
    def is_loop(self) -> bool:
        return self.value.endswith(".loop")

    @property
    def is_skip(self) -> bool:
        return self.value.endswith(".skip")
