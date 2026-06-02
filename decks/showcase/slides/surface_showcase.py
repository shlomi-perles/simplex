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

config.renderer = "opengl"
config.write_to_movie = True

from simplex import ThreeDSlide
from simplex.engine.region import Region
from simplex.engine.scaling import scale_to_fit_mobject
from simplex.engine.text import Caption
from simplex.mobjects.surface import ColorBar, ScalarFieldSurface, colorize_surface

try:
    from slides.showcase_style import setup_showcase_chrome
except ModuleNotFoundError:  # direct ``manim slides/surface_showcase.py ...`` execution
    from showcase_style import setup_showcase_chrome


class SurfaceColoring(ThreeDSlide):
    """ScalarFieldSurface + ColorBar + colorize_surface with matplotlib colormaps."""

    def setup(self) -> None:
        super().setup()
        self.region = Region.full_frame().fix_in_frame()
        setup_showcase_chrome(
            self,
            r"mobjects/surface.py -- ScalarFieldSurface + ColorBar + colorize_surface",
        )

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

        self.play(Write(self.showcase_title), Create(surface), Write(bar))
        self.next_slide()

        # ── Sub-slide 2: live colormap switch ─────────────────────
        self.begin_ambient_camera_rotation(rate=0.15)
        self.wait(2)

        new_bar = ColorBar(
            colormap="viridis",
            min_value=-1,
            max_value=1,
            height=2.8,
        ).move_to(bar)

        new_bar.fix_in_frame()  # Keep the new bar fixed in the frame during the transformation
        self.play(ReplacementTransform(bar, new_bar), surface.animate.set_colormap("viridis"))
        self.next_slide()

        # ── Sub-slide 3: colorize_surface on a plain OpenGLSurface ─

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
        bar2.align_to(new_bar, LEFT).match_y(new_bar)

        bar2.fix_in_frame()
        self.play(ReplacementTransform(new_bar, bar2), ReplacementTransform(surface, plain))
        self.begin_ambient_camera_rotation(rate=0.2)
        self.wait(2)
        self.next_slide()

        self.play(FadeOut(plain), FadeOut(bar2))
        # self.remove_fixed_in_frame_mobjects(bar)

        # ── Sub-slide 4: matplotlib colormap gallery ──────────────
        title = Tex(r"Any \texttt{matplotlib} colormap works out of the box")
        title.scale_to_fit_width(self.region.width * 0.7)
        self.region.place(title, UP)
        self.region.update(top=title)

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
            label.scale_to_fit_width(cb.width * 1.2).next_to(cb, DOWN)
            col.add(cb, label)
            gallery.add(col)

        gallery.arrange(RIGHT, buff=0.7)
        scale_to_fit_mobject(gallery, self.region, buff=LARGE_BUFF)
        self.region.place(gallery)

        title.fix_in_frame()
        gallery.fix_in_frame()
        self.play(Write(title), FadeIn(gallery))
        self.next_slide()

        self.play(FadeOut(title), FadeOut(gallery))
        self.clear_scene()
