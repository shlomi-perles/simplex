"""Top-level authoring imports."""

from simplex import (
    SIMPLEX_DARK,
    SIMPLEX_LIGHT,
    BaseSlide,
    Caption,
    Paper,
    ShowPaper,
    Slide,
    ThreeDSlide,
    make_chrome,
    presets,
)
from simplex.slides import BaseSlide as BaseSlideFromSlides
from simplex.slides import Slide as SlideFromSlides
from simplex.slides import ThreeDSlide as ThreeDSlideFromSlides


def test_top_level_authoring_imports() -> None:
    assert Slide is SlideFromSlides
    assert ThreeDSlide is ThreeDSlideFromSlides
    assert BaseSlide is Slide
    assert BaseSlideFromSlides is Slide
    assert Caption.__name__ == "Caption"
    assert Paper.__name__ == "Paper"
    assert ShowPaper.__name__ == "ShowPaper"
    assert SIMPLEX_DARK is presets.SIMPLEX_DARK
    assert SIMPLEX_LIGHT is presets.SIMPLEX_LIGHT
    assert callable(make_chrome)
