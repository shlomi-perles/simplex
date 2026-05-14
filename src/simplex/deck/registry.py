"""Discover sections + decks on disk.

Layout:

    decks/
      <featured-slug>/deck.toml         # featured section
      <section>/_section.toml           # carousel metadata (optional)
      <section>/<slug>/deck.toml         # sectioned decks

Recursion is exactly one level deep. Decks placed deeper than that raise.
The walker preserves legacy single-file `slides.py` decks as well as the
new `slides/` package layout.
"""

from pathlib import Path

from pydantic import BaseModel, ConfigDict

from simplex.deck.config import DeckConfig
from simplex.deck.section import FEATURED_SLUG, SectionConfig

_SKIP_PREFIXES = ("_", ".")


def _is_skipped(name: str) -> bool:
    return name.startswith(_SKIP_PREFIXES)


def _is_deck_dir(p: Path) -> bool:
    return p.is_dir() and not _is_skipped(p.name) and (p / "deck.toml").exists()


class Section(BaseModel):
    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)
    config: SectionConfig
    decks: tuple[DeckConfig, ...]


class SectionedRegistry(BaseModel):
    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)
    sections: tuple[Section, ...]

    @property
    def all_decks(self) -> tuple[DeckConfig, ...]:
        return tuple(d for s in self.sections for d in s.decks)

    def find_deck(self, slug: str) -> DeckConfig | None:
        for deck in self.all_decks:
            if deck.slug == slug:
                return deck
        return None


def _section_sort_key(
    section: Section,
    default_order: tuple[str, ...],
) -> tuple[int, int, str]:
    cfg = section.config
    if cfg.slug in default_order:
        return (0, default_order.index(cfg.slug), cfg.title)
    return (1, cfg.order, cfg.title)


def discover(
    decks_dir: Path,
    *,
    default_section_order: tuple[str, ...] = (),
) -> SectionedRegistry:
    """Return every section + deck discoverable under `decks_dir`."""
    if not decks_dir.exists():
        return SectionedRegistry(sections=())

    featured_decks: list[DeckConfig] = []
    sections: list[Section] = []

    for entry in sorted(decks_dir.iterdir()):
        if _is_skipped(entry.name):
            continue
        if _is_deck_dir(entry):
            featured_decks.append(DeckConfig.load(entry, section_slug=FEATURED_SLUG))
            continue
        if not entry.is_dir():
            continue
        cfg = SectionConfig.load(entry)
        decks: list[DeckConfig] = []
        for child in sorted(entry.iterdir()):
            if _is_skipped(child.name):
                continue
            if _is_deck_dir(child):
                decks.append(DeckConfig.load(child, section_slug=cfg.slug))
                continue
            if child.is_dir() and any(child.rglob("deck.toml")):
                raise ValueError(
                    f"decks/ supports exactly one level of sections; "
                    f"found a deck.toml below {child}"
                )
        if decks:
            decks.sort(key=lambda d: (d.order, d.slug))
            sections.append(Section(config=cfg, decks=tuple(decks)))

    if featured_decks:
        featured_decks.sort(key=lambda d: (d.order, d.slug))
        featured = Section(
            config=SectionConfig.featured(),
            decks=tuple(featured_decks),
        )
        sections.insert(0, featured)

    sections.sort(key=lambda s: _section_sort_key(s, default_section_order))
    return SectionedRegistry(sections=tuple(sections))
