"""BaseSlide -- the common manim-slides root.

Theme + Manim config are applied in `__init__` *before* `super().__init__()`
runs. Manim's `Scene.__init__` constructs the camera from `config.background_color`
during super init, so setting that value in `setup()` (which runs later) is too
late -- the camera locks in the previous value (Manim's default black). Doing
the configure here is what makes `theme.palette.background` actually reach the
rendered video.

Per-deck theme/quality come in via `SIMPLEX_THEME` / `SIMPLEX_QUALITY` env
vars, set by `simplex.render.runner` from `deck.toml`. The class attributes
remain as fallbacks for slides run outside the simplex CLI.
"""

import os
from collections.abc import Iterable
from typing import Any

from manim_slides.slide import Slide

from simplex.engine.animations import Remove
from simplex.engine.config import configure_manim
from simplex.engine.defaults import apply_theme_defaults
from simplex.engine.region import Region
from simplex.theme import presets
from simplex.theme.context import active_theme


class BaseSlide(Slide):
    """manim-slides Scene with theme + region + clear_scene wired in."""

    theme_name: str = "dastimator_dark"
    quality: str = "high_quality"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        theme_name = os.environ.get("SIMPLEX_THEME", self.theme_name)
        quality = os.environ.get("SIMPLEX_QUALITY", self.quality)
        theme = presets.get(theme_name)
        self._theme_ctx = active_theme(theme)
        self._theme_ctx.__enter__()
        configure_manim(theme, quality)
        apply_theme_defaults(theme)
        super().__init__(*args, **kwargs)

    def setup(self) -> None:
        super().setup()
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
