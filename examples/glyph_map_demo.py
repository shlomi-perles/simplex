"""``TransformByGlyphMap`` -- glyph-aware transition between two MathTex.

This demo uses ``auto_morph=True`` so unmentioned glyphs get morphed as
a group, sparing us from looking up specific indices. For a deck where
you know which glyph maps where, supply explicit
``(from_indices, to_indices)`` entries -- the auto modes will pick up
the rest.

If you don't know the indices, drop ``auto_morph`` and the animation
falls back to ``show_indices`` mode -- it overlays coloured index labels
on both mobjects so you can read off the right assignments.
"""

from manim import LEFT, MathTex, Scene, Write

from simplex.engine.glyph_map import TransformByGlyphMap


class GlyphMapDemo(Scene):
    def construct(self) -> None:
        src = MathTex("a", "+", "b", "=", "c").to_edge(LEFT)
        dst = MathTex("c", "=", "a", "+", "b").to_edge(LEFT)

        self.play(Write(src))
        self.wait(0.3)
        self.play(TransformByGlyphMap(src, dst, auto_morph=True))
        self.wait()
