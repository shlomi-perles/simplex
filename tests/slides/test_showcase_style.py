from typing import Any

from decks.showcase.slides.showcase_style import _install_footer_preserving_clear_scene


class _SlideStub:
    def __init__(self) -> None:
        self.exclusions: list[tuple[Any, ...]] = []

    def clear_scene(self, *, exclude: tuple[Any, ...] = ()) -> None:
        self.exclusions.append(exclude)


def test_showcase_clear_scene_preserves_footer() -> None:
    slide = _SlideStub()
    footer = object()

    _install_footer_preserving_clear_scene(slide, footer)

    slide.clear_scene()

    assert slide.exclusions == [(footer,)]


def test_showcase_clear_scene_extends_existing_exclusions() -> None:
    slide = _SlideStub()
    footer = object()
    keep = object()

    _install_footer_preserving_clear_scene(slide, footer)

    slide.clear_scene(exclude=(keep,))

    assert slide.exclusions == [(keep, footer)]
