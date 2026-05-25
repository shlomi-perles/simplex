"""Top-level authoring imports."""

from simplex import SIMPLEX_DARK, BaseSlide, Caption, Paper, ShowPaper, make_chrome, presets
from simplex.slides import BaseSlide as BaseSlideFromSlides


def test_top_level_authoring_imports() -> None:
    assert BaseSlide is BaseSlideFromSlides
    assert Caption.__name__ == "Caption"
    assert Paper.__name__ == "Paper"
    assert ShowPaper.__name__ == "ShowPaper"
    assert SIMPLEX_DARK is presets.SIMPLEX_DARK
    assert callable(make_chrome)
