"""Deck-manifest Pydantic schema shared by rendering and web output.

The Manim plugin and web builder both import this schema
(``from simplex.manifest import DeckManifest, MainSlide, Subsection``)
instead of maintaining parallel definitions.

The manifest is produced by ``simplex.render.reconcile`` (web-builder side)
by merging Manim's native ``sections/<Scene>.json`` with manim-slides'
``slides/<Scene>.json``; consumed by the HTML / PDF / portal templates.

The schema is deliberately Manim-free so the web build doesn't pull in
Manim. Paths are stored as ``pathlib.Path`` for downstream type safety.
"""

from pathlib import Path
from typing import Self

from pydantic import BaseModel, ConfigDict, Field

from simplex.section import SimplexSectionType


class Subsection(BaseModel):
    """One sub-stop within a main slide -- a single video segment.

    Emitted by manim-slides as the segment between two ``next_slide()``
    calls. Multiple ``Subsection`` instances compose into a ``MainSlide``.
    """

    model_config = ConfigDict(frozen=True)

    name: str
    section_type: SimplexSectionType
    video: Path | None = None
    duration_s: float = 0.0

    @property
    def is_loop(self) -> bool:
        return self.section_type.is_loop

    @property
    def is_skip(self) -> bool:
        return self.section_type.is_skip


class MainSlide(BaseModel):
    """One numbered slide -- a RevealJS horizontal slide.

    Groups the consecutive sub-stops that follow a ``MAIN`` section type
    in the rendered scene. ``thumbnail`` is resolved at reconcile time
    (default: the last frame of the second-to-last subsection).
    """

    model_config = ConfigDict(frozen=True)

    index: int
    scene: str
    name: str
    section_type: SimplexSectionType
    subsections: tuple[Subsection, ...] = ()
    thumbnail: Path | None = None
    notes: str | None = None

    @property
    def duration_s(self) -> float:
        return sum(sub.duration_s for sub in self.subsections)

    @property
    def subsection_count(self) -> int:
        return len(self.subsections)


class DeckManifest(BaseModel):
    """Top-level deck artifact consumed by the web builder.

    Built by ``simplex.render.reconcile`` from Manim's sections JSON and
    manim-slides' ``PresentationConfig``. Serialise with
    ``DeckManifest.model_dump_json(indent=2)`` for on-disk persistence
    between render and build phases.
    """

    model_config = ConfigDict(frozen=True)

    deck_slug: str
    main_slides: tuple[MainSlide, ...] = ()
    schema_version: int = Field(
        default=1,
        description=(
            "Bumped on breaking shape changes. Web builder rejects unknown "
            "versions with a clear error pointing at the required package bump."
        ),
    )

    @property
    def slide_count(self) -> int:
        return len(self.main_slides)

    @property
    def total_duration_s(self) -> float:
        return sum(main.duration_s for main in self.main_slides)

    def find(self, name: str) -> MainSlide | None:
        """Return the main slide with ``name`` (case-sensitive), or ``None``."""
        return next((m for m in self.main_slides if m.name == name), None)

    def at(self, index: int) -> MainSlide:
        """Return the main slide at zero-based ``index``. Raises ``IndexError``."""
        return self.main_slides[index]

    @classmethod
    def empty(cls, slug: str) -> Self:
        """Empty manifest for the given deck slug -- useful for tests + scaffolding."""
        return cls(deck_slug=slug, main_slides=())
