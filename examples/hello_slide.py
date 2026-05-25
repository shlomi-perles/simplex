"""Minimal Simplex deck: one main slide, one sub-stop.

Demonstrates:
- `BaseSlide.next_slide()` -- first bare call auto-promotes to a main
  slide named after the scene class with spaces between PascalCase
  boundaries (``HelloSlide`` -> ``"Hello Slide"``). Pass ``name=`` to
  override the name.
- `BaseSlide.next_slide()` -- subsequent bare call -> sub-stop of the
  current main (RevealJS vertical navigation).
- `region.place(...)` to position via a Manim direction vector.
- `Region` body shrunk by `make_chrome` for a clean header + body band.
"""

from manim import ORIGIN, MathTex, Write

from simplex import BaseSlide, make_chrome, presets


class HelloSlide(BaseSlide):
    def setup(self) -> None:
        super().setup()
        chrome = make_chrome(presets.SIMPLEX_DARK, self.region, header="Hello, Simplex")
        self.add_to_canvas(**chrome.mobjects)
        self.region = chrome.body_region

    def construct(self) -> None:
        eq = MathTex(r"e^{i\pi} + 1 = 0")
        self.region.place(eq, ORIGIN)
        self.play(Write(eq))
        self.next_slide()  # first call -> MAIN named "Hello Slide" (auto)

        consequence = MathTex(r"\therefore\ \cos\pi + i\sin\pi = -1")
        self.region.place(consequence, ORIGIN)
        self.play(Write(consequence))
        self.next_slide()  # bare after first MAIN -> sub-stop
