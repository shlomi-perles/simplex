"""Optimizer race: GD, Momentum, AdaGrad, ADAM run simultaneously.

This is the visual climax: four dots from the same start zoom toward the
optimum at the same physical time. Differences in the trajectories tell
the whole story.
"""

import numpy as np
from manim import (
    DEGREES,
    DOWN,
    LEFT,
    RIGHT,
    UP,
    FadeIn,
    MoveAlongPath,
    ParametricFunction,
    Sphere,
    Tex,
    VGroup,
    Write,
)

from manim_slides import ThreeDSlide

from simplex.engine.text import BodyText, Caption
from simplex.slides import BaseSlide, ContentSlide

from common import (  # noqa: I001
    C_ADAM,
    C_AXIS,
    C_GD,
    C_MOMENTUM,
    C_OPTIMUM,
    C_VARIANCE,
    adagrad_step,
    adam_step,
    contour_quad,
    gd_step,
    glowing_dot,
    iterates_to_3d_path,
    loss_surface,
    make_2d_axes,
    make_3d_axes,
    momentum_step,
    run_optimizer,
    trail_from_points,
)
from equation_lab import kicker_equation


class OptimizerRace2D(ContentSlide):
    """All four optimizers from the same starting point, drawn together."""

    header = "Race: GD vs Momentum vs AdaGrad vs ADAM"
    page_number = 17

    def construct(self) -> None:
        ax = make_2d_axes(width=8.5, height=5.0)
        contours = contour_quad(ax, color=C_AXIS)
        self.region.place(VGroup(ax, contours), "center")
        ax.shift(DOWN * 0.2)
        contours.shift(DOWN * 0.2)
        self.add(ax, contours)

        opt_marker = glowing_dot(ax.c2p(0, 0), color=C_OPTIMUM, radius=0.09, glow_scale=2.2)
        self.play(FadeIn(opt_marker))

        # Run all four optimizers with comparable effective LRs (so the race
        # is fair).
        gd_pts = run_optimizer(lambda s: gd_step(s, lr=0.28), n_steps=24)
        mo_pts = run_optimizer(lambda s: momentum_step(s, lr=0.30, gamma=0.8), n_steps=24)
        ada_pts = run_optimizer(lambda s: adagrad_step(s, lr=1.2), n_steps=24)
        adam_pts = run_optimizer(lambda s: adam_step(s, lr=0.32, gamma=0.9, beta=0.99), n_steps=24)

        gd_trail = trail_from_points(ax, gd_pts, color=C_GD)
        mo_trail = trail_from_points(ax, mo_pts, color=C_MOMENTUM)
        ada_trail = trail_from_points(ax, ada_pts, color=C_VARIANCE)
        adam_trail = trail_from_points(ax, adam_pts, color=C_ADAM)

        legend = VGroup(
            Caption(r"\textbf{GD}", color=C_GD),
            Caption(r"\textbf{Momentum}", color=C_MOMENTUM),
            Caption(r"\textbf{AdaGrad}", color=C_VARIANCE),
            Caption(r"\textbf{ADAM}", color=C_ADAM),
        ).arrange(DOWN, buff=0.15, aligned_edge=LEFT)
        legend.scale(0.85).to_corner(UP + LEFT).shift(DOWN * 0.55 + RIGHT * 0.3)
        self.play(Write(legend))
        self.next_slide()

        # Reveal trails one at a time so each algorithm is studied.
        for trail, pts, color in (
            (gd_trail, gd_pts, C_GD),
            (mo_trail, mo_pts, C_MOMENTUM),
            (ada_trail, ada_pts, C_VARIANCE),
            (adam_trail, adam_pts, C_ADAM),
        ):
            head = glowing_dot(ax.c2p(*pts[-1]), color=color)
            self.play(Write(trail), FadeIn(head, run_time=0.4), run_time=1.6)
            self.next_slide()

        moral = BodyText(
            r"ADAM combines momentum's smoothness with AdaGrad's per-axis scaling.",
            color=C_ADAM,
        ).scale(0.7)
        moral.scale_to_fit_width(self.region.width * 0.75)
        self.region.place(moral, "bottom", buff=0.15)
        self.play(Write(moral))
        self.next_slide()


class OptimizerRace3D(ThreeDSlide, BaseSlide):
    """Same race on the 3D surface for spatial intuition."""

    def construct(self) -> None:
        self.set_camera_orientation(phi=58 * DEGREES, theta=-40 * DEGREES)

        axes = make_3d_axes(
            x_range=(-3.0, 3.0, 1.0),
            y_range=(-3.0, 3.0, 1.0),
            z_range=(0.0, 20.0, 5.0),
        )
        surface = loss_surface(axes)

        title = Tex(r"Same race, on the 3D bowl", font_size=40)
        title.to_corner(UP + LEFT)
        self.add_fixed_in_frame_mobjects(title)

        legend = VGroup(
            Tex(r"\textbf{GD}", color=C_GD, font_size=26),
            Tex(r"\textbf{Momentum}", color=C_MOMENTUM, font_size=26),
            Tex(r"\textbf{AdaGrad}", color=C_VARIANCE, font_size=26),
            Tex(r"\textbf{ADAM}", color=C_ADAM, font_size=26),
        ).arrange(DOWN, buff=0.15, aligned_edge=LEFT)
        legend.to_corner(UP + RIGHT).shift(LEFT * 0.3 + DOWN * 0.15)
        self.add_fixed_in_frame_mobjects(legend)

        self.play(FadeIn(axes))
        self.play(FadeIn(surface), run_time=1.2)
        self.play(Write(title), Write(legend))
        self.next_slide()

        # Trajectories.
        trajectories = (
            (run_optimizer(lambda s: gd_step(s, lr=0.28), n_steps=40), C_GD, "GD"),
            (
                run_optimizer(lambda s: momentum_step(s, lr=0.30, gamma=0.8), n_steps=40),
                C_MOMENTUM,
                "Momentum",
            ),
            (run_optimizer(lambda s: adagrad_step(s, lr=1.2), n_steps=40), C_VARIANCE, "AdaGrad"),
            (
                run_optimizer(lambda s: adam_step(s, lr=0.32, gamma=0.9, beta=0.99), n_steps=40),
                C_ADAM,
                "ADAM",
            ),
        )

        balls: list[tuple[Sphere, ParametricFunction]] = []
        for pts, color, _name in trajectories:
            path_fn = iterates_to_3d_path(axes, pts)
            path = ParametricFunction(path_fn, t_range=(0.0, 1.0))
            path.set_stroke(color=color, width=4)
            ball = Sphere(radius=0.10, resolution=(14, 14)).set_color(color)
            ball.move_to(path_fn(0.0))
            balls.append((ball, path))

        self.play(*(FadeIn(b) for b, _ in balls))
        self.next_slide()

        self.play(
            *(MoveAlongPath(b, p) for b, p in balls),
            *(Write(p) for _, p in balls),
            run_time=6.0,
        )
        self.next_slide()


class Recap(ContentSlide):
    """One-slide closing recap with semantic colors."""

    header = "Recap"
    page_number = 19

    def construct(self) -> None:
        rows = (
            (r"\textbf{GD}", r"Same LR for all axes -- stuck on ill-conditioned bowls.", C_GD),
            (
                r"\textbf{Momentum}",
                r"Velocity averages past gradients $\Rightarrow$"
                r" smoother, faster.",
                C_MOMENTUM,
            ),
            (
                r"\textbf{AdaGrad}",
                r"Per-axis LR $\eta / [s_t]_i$ from squared-gradient"
                r" history $\Rightarrow$ unit-invariant.",
                C_VARIANCE,
            ),
            (
                r"\textbf{ADAM}",
                r"Momentum (first moment) $+$ discounted AdaGrad"
                r" (second moment).",
                C_ADAM,
            ),
        )

        lines = VGroup()
        for tag, text, color in rows:
            tag_mob = BodyText(tag, color=color).scale(0.9)
            text_mob = BodyText(text).scale(0.75)
            line = VGroup(tag_mob, text_mob).arrange(RIGHT, buff=0.35)
            lines.add(line)
        lines.arrange(DOWN, buff=0.45, aligned_edge=LEFT)
        lines.scale_to_fit_width(self.region.width * 0.88)
        self.region.place(lines, "center")

        for line in lines:
            self.play(Write(line))
            self.next_slide()

        kicker = kicker_equation(font_size=48)
        self.region.place(kicker, "bottom", buff=0.25)
        self.play(Write(kicker))
        self.next_slide()
