"""Showcase: ScalarFieldSurface, colorize_surface, ColorBar, matplotlib colormaps.

Demonstrates the full scalar-field surface coloring API with the OpenGL
renderer:

- ``ScalarFieldSurface`` with height / distance / custom color functions
- ``colorize_surface`` applied to a plain ``OpenGLSurface``
- ``ColorBar`` legend with matplotlib colormap names
- Live ``set_colormap`` / ``refresh_colors`` on the same surface
"""

from typing import Any, cast

import numpy as np
import numpy.typing as npt
from manim import (
    DEGREES,
    DOWN,
    RIGHT,
    SMALL_BUFF,
    UP,
    Create,
    FadeIn,
    FadeOut,
    ReplacementTransform,
    Tex,
    VGroup,
    Write,
    config,
)
from manim.opengl import OpenGLSurface

config.renderer = "opengl"
config.write_to_movie = True

from simplex import ThreeDSlide
from simplex.engine.text import Caption
from simplex.mobjects.surface import ColorBar, ScalarFieldSurface, colorize_surface

try:
    from slides.showcase_style import setup_showcase_chrome
except ModuleNotFoundError:  # direct ``manim slides/surface_showcase.py ...`` execution
    from showcase_style import setup_showcase_chrome


type SurfacePoint = npt.NDArray[np.float64]


def _wave_surface_point(u: float, v: float) -> SurfacePoint:
    return np.asarray([u, v, np.sin(u) * np.cos(v)], dtype=np.float64)


def _gaussian_surface_point(u: float, v: float) -> SurfacePoint:
    return np.asarray([u, v, np.exp(-(u**2 + v**2))], dtype=np.float64)


class SurfaceColoring(ThreeDSlide):
    """ScalarFieldSurface + ColorBar + colorize_surface with matplotlib colormaps."""

    def setup(self) -> None:
        super().setup()
        self.region = self.region.fix_in_frame()
        setup_showcase_chrome(
            self,
            r"mobjects/surface.py -- ScalarFieldSurface + ColorBar + colorize_surface",
        )

    def construct(self) -> None:
        # ── Sub-slide 1: ScalarFieldSurface with height coloring ──
        self.set_camera_orientation(phi=60 * DEGREES, theta=-45 * DEGREES)

        surface = ScalarFieldSurface(
            _wave_surface_point,
            u_range=[-3, 3],
            v_range=[-3, 3],
            color_func="height",
            colormap="RdYlBu_r",
            color_range=(-1, 1),
        )

        bar = ColorBar(
            colormap="RdYlBu_r",
            min_value=-1,
            max_value=1,
        ).to_edge(RIGHT)
        bar.fix_in_frame()

        self.play(Write(self.canvas["showcase_title"]), Create(surface), Write(bar))
        self.next_slide()

        # ── Sub-slide 2: live colormap switch ─────────────────────
        self.begin_ambient_camera_rotation(rate=0.15)
        self.wait(2)

        new_bar = ColorBar(
            colormap="viridis",
            min_value=-1,
            max_value=1,
        ).move_to(bar)

        new_bar.fix_in_frame()  # Keep the new bar fixed in the frame during the transformation
        self.play(
            ReplacementTransform(bar, new_bar),
            cast(Any, surface.animate.set_colormap("viridis")),
        )
        self.next_slide()

        # ── Sub-slide 3: colorize_surface on a plain OpenGLSurface ─

        plain = OpenGLSurface(
            _gaussian_surface_point,
            u_range=[-3, 3],
            v_range=[-3, 3],
        )
        colorize_surface(
            plain,
            ScalarFieldSurface.distance_from((0.0, 0.0, 0.0)),
            colormap="plasma",
        )

        bar2 = ColorBar(colormap="plasma", min_value=0, max_value=4).move_to(new_bar)

        bar2.fix_in_frame()
        self.play(
            ReplacementTransform(new_bar, bar2),
            ReplacementTransform(cast(Any, surface), cast(Any, plain)),
        )
        self.begin_ambient_camera_rotation(rate=0.2)
        self.wait(2)
        self.next_slide()

        self.play(FadeOut(cast(Any, plain)), FadeOut(bar2))
        # self.remove_fixed_in_frame_mobjects(bar)

        # ── Sub-slide 4: matplotlib colormap gallery ──────────────
        title = Tex(r"Any \texttt{matplotlib} colormap works out of the box")
        title.scale_to_fit_width(self.region.width * 0.7)
        self.region.place(title, UP)
        self.region.update(top=title)
        self.region.shrink(top=1, bottom=1)

        cmap_names = ["viridis", "plasma", "coolwarm", "inferno", "twilight"]
        gallery = VGroup()
        label_font_size: float | None = None
        cb_height: float | None = None
        for point, name in zip(
            self.region.linspace(RIGHT, len(cmap_names), inset=1), cmap_names, strict=True
        ):
            cb = ColorBar(
                colormap=name,
                n_labels=3,
            )
            label = Caption(name.replace("_", r"\_"))
            label.scale_to_fit_width(cb.width * 1.2)
            label_font_size = label.font_size if label_font_size is None else label_font_size
            cb_group = VGroup(cb, label).scale_to_fit_height(self.region.height)
            cb_height = cb.height if cb_height is None else cb_height
            cb_group.set_height(cb_height)
            label.font_size = label_font_size
            label.next_to(cb, DOWN, buff=SMALL_BUFF)

            gallery.add(VGroup(cb, label).move_to(point))

        title.fix_in_frame()
        gallery.fix_in_frame()
        self.play(Write(title), FadeIn(gallery))
        self.next_slide()
        self.clear_scene()
