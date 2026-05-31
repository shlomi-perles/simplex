"""Helpers for single-theme and true dark/light render variants."""

from pathlib import Path

from simplex.deck.config import (
    DeckConfig,
    ResolvedSlideThemes,
    SlideThemeConfig,
    SlideThemeSelection,
    SlideThemeVariant,
)


def resolve_slide_themes(
    deck: DeckConfig,
    site_slide_themes: SlideThemeConfig | None = None,
) -> ResolvedSlideThemes:
    """Merge package defaults, site settings, then deck settings."""
    site_resolved = (site_slide_themes or SlideThemeConfig()).resolve()
    return deck.slide_themes.resolve(site_resolved)


def selected_variants(
    config: ResolvedSlideThemes,
    selection: SlideThemeSelection,
) -> tuple[SlideThemeVariant, ...]:
    """Return the true-theme variants requested by the CLI selection."""
    return config.selected_variants(selection)


def variant_output_dir(deck_output_dir: Path, variant: SlideThemeVariant) -> Path:
    """Directory for one true-theme render under a deck's site output."""
    return deck_output_dir / "themes" / variant


def variant_deck(
    deck: DeckConfig,
    config: ResolvedSlideThemes,
    variant: SlideThemeVariant,
) -> DeckConfig:
    """Return a copy of ``deck`` pinned to one concrete Manim theme."""
    return deck.model_copy(update={"theme": config.theme_name(variant)})
