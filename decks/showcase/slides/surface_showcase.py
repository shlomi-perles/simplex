"""Showcase: ScalarFieldSurface, colorize_surface, ColorBar, matplotlib colormaps.

Demonstrates the full scalar-field surface coloring API with the OpenGL
renderer:

- ``ScalarFieldSurface`` with height / distance / custom color functions
- ``colorize_surface`` applied to a plain ``OpenGLSurface``
- ``ColorBar`` legend with matplotlib colormap names
- Live ``set_colormap`` / ``refresh_colors`` on the same surface
"""

from manim import *
from manim.opengl import *

from simplex.engine.scaling import scale_to_fit
from simplex.engine.text import Caption
from simplex.mobjects.surface import ColorBar, ScalarFieldSurface, colorize_surface
from simplex.slides import BaseSlide

config.renderer = "opengl"
config.write_to_movie = True


class SurfaceColoring(BaseSlide, ThreeDScene):
    """ScalarFieldSurface + ColorBar + colorize_surface with matplotlib colormaps."""

    def setup(self) -> None:
        super().setup()

    def construct(self) -> None:
        # ── Sub-slide 1: ScalarFieldSurface with height coloring ──
        self.set_camera_orientation(phi=60 * DEGREES, theta=-45 * DEGREES)

        surface = ScalarFieldSurface(
            lambda u, v: np.array([u, v, np.sin(u) * np.cos(v)]),
            u_range=[-3, 3],
            v_range=[-3, 3],
            resolution=(60, 60),
            color_func="height",
            colormap="RdYlBu_r",
            color_range=(-1, 1),
            opacity=0.85,
        )

        bar = ColorBar(
            colormap="RdYlBu_r",
            min_value=-1,
            max_value=1,
            height=2.8,
        ).to_edge(RIGHT, buff=0.4)
        self.add_fixed_in_frame_mobjects(bar)

        self.play(FadeIn(surface), FadeIn(bar))
        self.next_slide()

        # ── Sub-slide 2: live colormap switch ─────────────────────
        self.begin_ambient_camera_rotation(rate=0.15)
        self.wait(2)
        self.stop_ambient_camera_rotation()

        surface.set_colormap("viridis")
        new_bar = ColorBar(
            colormap="viridis",
            min_value=-1,
            max_value=1,
            height=2.8,
        ).to_edge(RIGHT, buff=0.4)
        self.add_fixed_in_frame_mobjects(new_bar)
        self.play(FadeOut(bar), FadeIn(new_bar))
        bar = new_bar
        self.next_slide()

        # ── Sub-slide 3: colorize_surface on a plain OpenGLSurface ─
        self.play(FadeOut(surface), FadeOut(bar))
        self.remove_fixed_in_frame_mobjects(bar)

        plain = OpenGLSurface(
            lambda u, v: np.array([u, v, np.exp(-(u**2 + v**2))]),
            u_range=[-3, 3],
            v_range=[-3, 3],
            resolution=(60, 60),
            opacity=0.9,
        )
        colorize_surface(
            plain,
            ScalarFieldSurface.distance_from(ORIGIN),
            colormap="plasma",
        )

        bar2 = ColorBar(colormap="plasma", min_value=0, max_value=4, height=2.8)
        bar2.to_edge(RIGHT, buff=0.4)
        self.add_fixed_in_frame_mobjects(bar2)

        self.play(FadeIn(plain), FadeIn(bar2))
        self.begin_ambient_camera_rotation(rate=0.2)
        self.wait(2)
        self.stop_ambient_camera_rotation()
        self.next_slide()

        self.play(FadeOut(plain), FadeOut(bar2))
        self.remove_fixed_in_frame_mobjects(bar2)

        # ── Sub-slide 4: matplotlib colormap gallery ──────────────
        cmap_names = ["viridis", "plasma", "coolwarm", "inferno", "twilight"]
        gallery = VGroup()

        for name in cmap_names:
            col = VGroup()
            cb = ColorBar(
                colormap=name,
                min_value=0,
                max_value=1,
                height=2.2,
                width=0.35,
                n_labels=3,
                font_size=18,
            )
            label = Caption(name.replace("_", r"\_"))
            label.scale(0.7)
            label.next_to(cb, DOWN, buff=0.25)
            col.add(cb, label)
            gallery.add(col)

        gallery.arrange(RIGHT, buff=0.7)
        scale_to_fit(gallery, len_x=11, len_y=4.5)
        gallery.move_to(ORIGIN)

        title = Tex(r"Any \texttt{matplotlib} colormap works out of the box")
        title.scale(0.75)
        title.next_to(gallery, UP, buff=0.35)

        self.add_fixed_in_frame_mobjects(title, gallery)
        self.play(Write(title), FadeIn(gallery))
        self.next_slide()

        self.remove_fixed_in_frame_mobjects(title, gallery)
        self.play(FadeOut(title), FadeOut(gallery))
        self.clear_scene()
