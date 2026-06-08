"""Minimal Simplex deck: one slide and one fragment cue.

Demonstrates:
- `SimplexScene.slide(...)` -- primary timeline cue.
- `SimplexScene.fragment(...)` -- sub-stop within the current slide.
- `region.place(...)` to position via a Manim direction vector.
- `Region` body shrunk by `make_chrome` for a clean header + body band.
"""

from manim import ORIGIN, MathTex, Write

from simplex import SimplexScene, make_chrome, presets


class HelloSlide(SimplexScene):
    def setup(self) -> None:
        super().setup()
        chrome = make_chrome(presets.SIMPLEX_DARK, self.region, header="Hello, Simplex")
        self.add_to_canvas(**chrome.mobjects)
        self.region = chrome.body_region

    def construct(self) -> None:
        self.slide(title="Hello Slide")
        eq = MathTex(r"e^{i\pi} + 1 = 0")
        self.region.place(eq, ORIGIN)
        self.play(Write(eq))

        self.fragment(title="Euler consequence")
        consequence = MathTex(r"\therefore\ \cos\pi + i\sin\pi = -1")
        self.region.place(consequence, ORIGIN)
        self.play(Write(consequence))
