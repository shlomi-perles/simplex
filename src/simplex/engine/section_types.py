"""Simplex section type enum for slide hierarchy.

Values are strings so they survive Manim's `Section(type_=...)` serialisation
into the sections JSON (`Section.get_dict` stores `type` verbatim). The
reconciler reads them back and groups consecutive sub-sections under their
preceding main.

The enum is intentionally manim-free: importing this module must not pull in
manim, so the CLI and reconcile pipelines can use it without paying for a
manim import.
"""

from enum import StrEnum


class SimplexSectionType(StrEnum):
    """Section types our `BaseSlide.next_slide` writes into the section JSON.

    A "main" slide is what the user perceives as one numbered slide. "sub"
    slides are sub-stops within that main (RevealJS vertical navigation).
    The LOOP / SKIP variants mirror manim-slides' loop / skip_animations
    behaviour while still encoding the main-vs-sub classification.
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
