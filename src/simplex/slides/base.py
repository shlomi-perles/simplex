"""BaseSlide -- the common manim-slides root."""

from collections.abc import Iterable
from typing import Any

from manim_slides.slide import Slide

from simplex.engine.animations import Remove
from simplex.engine.config import configure_manim
from simplex.engine.defaults import apply_theme_defaults
from simplex.engine.region import Region
from simplex.theme import presets
from simplex.theme.context import active_theme, get_active_theme


class BaseSlide(Slide):
    """manim-slides Scene with theme + region + clear_scene wired in."""

    theme_name: str = "dastimator_dark"
    quality: str = "high_quality"

    def setup(self) -> None:
        super().setup()
        self._theme_ctx = active_theme(presets.get(self.theme_name))
        self._theme_ctx.__enter__()
        theme = get_active_theme()
        configure_manim(theme, self.quality)
        apply_theme_defaults(theme)
        self.region = Region.full_frame()

    def tear_down(self) -> None:
        ctx = getattr(self, "_theme_ctx", None)
        if ctx is not None:
            ctx.__exit__(None, None, None)
        super().tear_down()

    def clear_scene(self, *, exclude: Iterable[Any] = ()) -> None:
        """Play `Remove(...)` for every mobject not in `exclude`."""
        skip = set(exclude)
        targets = [m for m in self.mobjects if m not in skip]
        if targets:
            self.play(*(Remove(m) for m in targets))
