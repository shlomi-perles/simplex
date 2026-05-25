"""Switching themes mid-scene with the ``active_theme`` context manager.

The plugin entry-point applies whatever theme is active at ``import manim``
time, but authors can push a different theme for a specific scope -- useful
when a single deck wants two color schemes (e.g. a dark intro and a light
proof).
"""

from manim import FadeIn, Scene, Tex

from simplex import active_theme, presets


class ThemeDemo(Scene):
    def construct(self) -> None:
        with active_theme(presets.SIMPLEX_DARK):
            dark_label = Tex("dark theme")
        with active_theme(presets.ACADEMIC_LIGHT):
            light_label = Tex("light theme")

        dark_label.shift([0, 1, 0])
        light_label.shift([0, -1, 0])
        self.play(FadeIn(dark_label), FadeIn(light_label))
        self.wait()
