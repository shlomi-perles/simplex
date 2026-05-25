"""Simplex section-type enum -- the slide-hierarchy seam.

Promoted from ``simplex.engine.section_types`` to the package root because
this enum is the cross-package contract: the plugin emits these strings into
Manim's native sections JSON, and the ``simplex`` web builder consumes them
when reconciling main/sub slide trees.

Values are strings so they round-trip through Manim's
``Section(type_=...)`` serialisation (``Section.get_dict`` stores ``type``
verbatim).

Intentionally Manim-free: importing this module must not pull in Manim, so
the CLI and reconcile pipelines can use it without paying the Manim import
cost.
"""

from enum import StrEnum


class SimplexSectionType(StrEnum):
    """Section types ``BaseSlide.next_slide`` writes into the section JSON.

    A *main* slide is what the viewer perceives as one numbered slide.
    *Sub* slides are sub-stops within that main (RevealJS vertical
    navigation). The ``LOOP`` / ``SKIP`` variants mirror manim-slides'
    ``loop`` / ``skip_animations`` behaviour while still encoding the
    main-vs-sub classification.
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
