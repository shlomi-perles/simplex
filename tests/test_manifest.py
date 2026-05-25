"""DeckManifest schema -- construction, frozen-ness, helpers, JSON round-trip."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from simplex.manifest import DeckManifest, MainSlide, Subsection
from simplex.section import SimplexSectionType


def test_empty_manifest_for_slug() -> None:
    m = DeckManifest.empty("dijkstra")
    assert m.deck_slug == "dijkstra"
    assert m.main_slides == ()
    assert m.slide_count == 0
    assert m.total_duration_s == 0.0


def test_subsection_loop_skip_inherit_from_section_type() -> None:
    s = Subsection(name="x", section_type=SimplexSectionType.SUB_LOOP, duration_s=1.0)
    assert s.is_loop
    assert not s.is_skip


def test_main_slide_duration_sums_subsections() -> None:
    main = MainSlide(
        index=0,
        scene="Intro",
        name="Hello",
        section_type=SimplexSectionType.MAIN,
        subsections=(
            Subsection(name="a", section_type=SimplexSectionType.SUB, duration_s=1.5),
            Subsection(name="b", section_type=SimplexSectionType.SUB, duration_s=2.5),
        ),
    )
    assert main.duration_s == pytest.approx(4.0)
    assert main.subsection_count == 2


def test_deck_manifest_total_duration_sums_mains() -> None:
    manifest = DeckManifest(
        deck_slug="d",
        main_slides=(
            MainSlide(
                index=0,
                scene="S",
                name="A",
                section_type=SimplexSectionType.MAIN,
                subsections=(
                    Subsection(name="a", section_type=SimplexSectionType.SUB, duration_s=1.0),
                ),
            ),
            MainSlide(
                index=1,
                scene="S",
                name="B",
                section_type=SimplexSectionType.MAIN,
                subsections=(
                    Subsection(name="b", section_type=SimplexSectionType.SUB, duration_s=2.0),
                ),
            ),
        ),
    )
    assert manifest.total_duration_s == pytest.approx(3.0)
    assert manifest.slide_count == 2


def test_find_returns_main_by_name() -> None:
    manifest = DeckManifest(
        deck_slug="d",
        main_slides=(
            MainSlide(index=0, scene="S", name="Theorem", section_type=SimplexSectionType.MAIN),
            MainSlide(index=1, scene="S", name="Proof", section_type=SimplexSectionType.MAIN),
        ),
    )
    found = manifest.find("Proof")
    assert found is not None
    assert found.index == 1


def test_find_returns_none_for_missing_name() -> None:
    manifest = DeckManifest.empty("d")
    assert manifest.find("Nope") is None


def test_at_index() -> None:
    main = MainSlide(index=0, scene="S", name="A", section_type=SimplexSectionType.MAIN)
    manifest = DeckManifest(deck_slug="d", main_slides=(main,))
    assert manifest.at(0) is main


def test_at_index_out_of_range() -> None:
    manifest = DeckManifest.empty("d")
    with pytest.raises(IndexError):
        manifest.at(0)


def test_frozen_models_reject_mutation() -> None:
    manifest = DeckManifest.empty("d")
    with pytest.raises(ValidationError):
        manifest.deck_slug = "other"  # type: ignore[misc]


def test_json_round_trip_preserves_paths_and_enums() -> None:
    manifest = DeckManifest(
        deck_slug="d",
        main_slides=(
            MainSlide(
                index=0,
                scene="S",
                name="A",
                section_type=SimplexSectionType.MAIN,
                thumbnail=Path("media/thumbs/a.png"),
                subsections=(
                    Subsection(
                        name="a",
                        section_type=SimplexSectionType.SUB,
                        video=Path("media/videos/a.mp4"),
                        duration_s=1.5,
                    ),
                ),
            ),
        ),
    )
    blob = manifest.model_dump_json()
    revived = DeckManifest.model_validate_json(blob)
    assert revived == manifest
    assert revived.main_slides[0].thumbnail == Path("media/thumbs/a.png")
    assert revived.main_slides[0].subsections[0].section_type is SimplexSectionType.SUB


def test_schema_version_default() -> None:
    assert DeckManifest.empty("d").schema_version == 1
