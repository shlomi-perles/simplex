"""Momentum GD slides: intuition (2D), 3D rolling-ball, equations.

The pedagogical thread:
    GD step:        x_{t+1} = x_t - eta * grad(x_t)
    Momentum step:  v_{t+1} = gamma * v_t + (1-gamma) * grad(x_t)
                    x_{t+1} = x_t - eta * v_{t+1}

Visually, GD recomputes a fresh arrow from the current point; momentum
recycles past direction (the "velocity" vector). On 3D the contrast is
striking because the ball's inertia carries it across narrow valleys.
"""

import numpy as np
from manim import (
    DEGREES,
    DOWN,
    LEFT,
    RIGHT,
    UP,
    Arrow,
    FadeIn,
    FadeOut,
    MathTex,
    MoveAlongPath,
    ParametricFunction,
    ReplacementTransform,
    Sphere,
    Tex,
    VGroup,
    Write,
)
from manim_slides import ThreeDSlide

from simplex.engine.text import BodyText, Caption
from simplex.slides import BaseSlide, ContentSlide

from common import (
    C_AXIS,
    C_GD,
    C_MOMENTUM,
    C_OPTIMUM,
    GAMMA_MOMENTUM,
    contour_quad,
    gd_step,
    glowing_dot,
    grad,
    gradient_arrow,
    iterates_to_3d_path,
    loss_surface,
    make_2d_axes,
    make_3d_axes,
    momentum_step,
    OptState,
    run_optimizer,
    trail_from_points,
)
from equation_lab import gd_equation, momentum_equation


class MomentumIntuition2D(ContentSlide):
    """2D contour view: GD vs Momentum side-by-side."""

    header = "Momentum: a ball remembers where it was going"
    page_number = 5

    def construct(self) -> None:
        # Two side-by-side panels.
        ax_gd = make_2d_axes(width=4.3, height=3.6)
        ax_mo = make_2d_axes(width=4.3, height=3.6)
        contours_gd = contour_quad(ax_gd, color=C_AXIS)
        contours_mo = contour_quad(ax_mo, color=C_AXIS)

        panel_gd = VGroup(ax_gd, contours_gd)
        panel_mo = VGroup(ax_mo, contours_mo)
        panels = VGroup(panel_gd, panel_mo).arrange(RIGHT, buff=0.8)
        self.region.place(panels, "center")
        panels.shift(DOWN * 0.3)

        title_gd = Caption(r"Vanilla GD", color=C_GD).next_to(panel_gd, UP, buff=0.2)
        title_mo = Caption(r"Momentum GD", color=C_MOMENTUM).next_to(panel_mo, UP, buff=0.2)

        opt_gd = glowing_dot(ax_gd.c2p(0, 0), color=C_OPTIMUM, radius=0.07, glow_scale=2.0)
        opt_mo = glowing_dot(ax_mo.c2p(0, 0), color=C_OPTIMUM, radius=0.07, glow_scale=2.0)

        self.play(FadeIn(panels), Write(title_gd), Write(title_mo))
        self.play(FadeIn(opt_gd), FadeIn(opt_mo))
        self.next_slide()

        # Run both optimizers from the same starting point.
        gd_pts = run_optimizer(lambda s: gd_step(s, lr=0.32), n_steps=20)
        mo_pts = run_optimizer(
            lambda s: momentum_step(s, lr=0.32, gamma=GAMMA_MOMENTUM),
            n_steps=20,
        )
        trail_gd = trail_from_points(ax_gd, gd_pts, color=C_GD)
        trail_mo = trail_from_points(ax_mo, mo_pts, color=C_MOMENTUM)
        head_gd = glowing_dot(ax_gd.c2p(*gd_pts[-1]), color=C_GD)
        head_mo = glowing_dot(ax_mo.c2p(*mo_pts[-1]), color=C_MOMENTUM)

        self.play(Write(trail_gd), Write(trail_mo), run_time=2.8)
        self.play(FadeIn(head_gd), FadeIn(head_mo))
        self.next_slide()

        moral = BodyText(r"Damps the steep axis, accelerates the flat one.").scale(0.6)
        self.region.place(moral, "bottom", buff=0.2)
        self.play(Write(moral))
        self.next_slide()


class MomentumStepBreakdown(ContentSlide):
    """Zoom in on ONE momentum step: from x_t, compute v_{t+1}, move.

    Layout:
        - Big contour axes occupy the LEFT 2/3 of the region.
        - The formula + annotations sit on the RIGHT 1/3.
    """

    header = "One momentum step, drawn slowly"
    page_number = 6

    def construct(self) -> None:
        ax = make_2d_axes(
            x_range=(-3.0, 3.0, 1.0),
            y_range=(-2.5, 2.5, 1.0),
            width=6.0,
            height=4.6,
        )
        contours = contour_quad(ax, a_x=1.0, a_y=1.0, color=C_AXIS)
        panel = VGroup(ax, contours)
        self.region.place(panel, "left", buff=0.5)
        self.add(ax, contours)

        # Warm up velocity with 1 momentum step from far away, then we draw
        # the step at iteration 2 (so velocity is non-zero AND visible).
        state = OptState(x=np.array([-2.5, 1.8]))
        momentum_step(state, lr=0.35, gamma=0.7)

        x_t = state.x.copy()
        v_t = state.velocity.copy()

        # Visuals: dot at x_t.
        dot_xt = glowing_dot(ax.c2p(*x_t), color=C_MOMENTUM)
        label_xt = MathTex(r"x_t", color=C_MOMENTUM, font_size=32).next_to(
            dot_xt, UP + LEFT, buff=0.08
        )
        self.play(FadeIn(dot_xt), Write(label_xt))
        self.next_slide()

        # Gradient arrow (descent direction) from x_t.
        g = grad(x_t[0], x_t[1])
        grad_arrow = gradient_arrow(ax, x_t, g, color=C_GD, scale=0.7, stroke_width=6)
        grad_label = MathTex(
            r"-\nabla f(x_t)",
            color=C_GD,
            font_size=28,
        ).next_to(grad_arrow.get_end(), DOWN, buff=0.1)
        self.play(Write(grad_arrow), Write(grad_label))
        self.next_slide()

        # Velocity arrow (from x_t along the running average direction).
        v_scale = 0.9
        v_end = ax.c2p(x_t[0] - v_scale * v_t[0], x_t[1] - v_scale * v_t[1])
        v_arrow = Arrow(
            start=ax.c2p(*x_t),
            end=v_end,
            buff=0.0,
            stroke_width=8,
            max_tip_length_to_length_ratio=0.28,
        )
        v_arrow.set_color(C_MOMENTUM)
        v_arrow.set_stroke(color=C_MOMENTUM, width=8)
        v_label = MathTex(
            r"-v_{t+1}",
            color=C_MOMENTUM,
            font_size=28,
        ).next_to(v_arrow.get_end(), DOWN + LEFT, buff=0.1)
        self.play(Write(v_arrow), Write(v_label))
        self.next_slide()

        # Right-side formula stack.
        rhs_eq = MathTex(
            r"v_{t+1}",
            r"=",
            r"\gamma\, v_t",
            r"+",
            r"(1-\gamma)\,\nabla f(x_t)",
            font_size=30,
        )
        rhs_eq[0].set_color(C_MOMENTUM)
        rhs_eq[2].set_color(C_MOMENTUM)
        rhs_eq[4].set_color(C_GD)
        gamma_note = BodyText(r"$\gamma \approx 0.85$").scale(0.7).set_color(C_MOMENTUM)
        rhs_text = BodyText(
            r"Past velocity \emph{dominates}; the new gradient just \emph{nudges} it."
        ).scale(0.55)
        rhs = VGroup(rhs_eq, gamma_note, rhs_text).arrange(DOWN, buff=0.35, aligned_edge=LEFT)
        rhs.scale_to_fit_width(self.region.width * 0.32)
        self.region.place(rhs, "right", buff=0.4)
        self.play(Write(rhs))
        self.next_slide()

        # Apply the step: move dot to x_{t+1}. Use a larger LR for clarity.
        new_state = OptState(x=state.x.copy(), velocity=state.velocity.copy())
        momentum_step(new_state, lr=0.5, gamma=0.7)
        x_next = new_state.x
        dot_next = glowing_dot(ax.c2p(*x_next), color=C_MOMENTUM)
        label_next = MathTex(
            r"x_{t+1}",
            color=C_MOMENTUM,
            font_size=32,
        ).next_to(dot_next, DOWN + RIGHT, buff=0.08)

        connecting = trail_from_points(
            ax,
            np.array([x_t, x_next]),
            color=C_OPTIMUM,
            opacity=0.9,
        )
        self.play(
            FadeOut(grad_arrow),
            FadeOut(grad_label),
            FadeOut(v_arrow),
            FadeOut(v_label),
        )
        self.play(Write(connecting), FadeIn(dot_next), Write(label_next))
        self.next_slide()


class MomentumIn3D(ThreeDSlide, BaseSlide):
    """3D rolling ball: shows the look-ahead intuition.

    Implementation note: we animate ball + trail with a single `MoveAlongPath`
    over a precomputed ParametricFunction. One big animation is friendlier
    to manim_slides' reversal step than 30 sequential ones.
    """

    def construct(self) -> None:
        self.set_camera_orientation(phi=62 * DEGREES, theta=-35 * DEGREES)

        axes = make_3d_axes(
            x_range=(-3.0, 3.0, 1.0),
            y_range=(-3.0, 3.0, 1.0),
            z_range=(0.0, 20.0, 5.0),
        )
        surface = loss_surface(axes)

        title = Tex(r"Momentum in 3D: the ball that remembers", font_size=40)
        title.to_corner(UP + LEFT)
        self.add_fixed_in_frame_mobjects(title)

        self.play(FadeIn(axes))
        self.play(FadeIn(surface), run_time=1.2)
        self.play(Write(title))
        self.next_slide()

        # Trajectory of momentum on the bowl. Pre-compute path points.
        pts = run_optimizer(
            lambda s: momentum_step(s, lr=0.20, gamma=0.85),
            n_steps=40,
        )
        path_fn = iterates_to_3d_path(axes, pts)
        path = ParametricFunction(path_fn, t_range=(0.0, 1.0))
        path.set_stroke(color=C_MOMENTUM, width=5)

        ball = Sphere(radius=0.14, resolution=(16, 16)).set_color(C_MOMENTUM)
        ball.move_to(path_fn(0.0))
        self.play(FadeIn(ball))
        self.next_slide()

        # Single big animation: ball walks the path while the trail is drawn.
        self.play(
            MoveAlongPath(ball, path),
            Write(path),
            run_time=5.0,
        )
        self.next_slide()

        # Annotation about the look-ahead.
        annotation = Tex(
            r"The velocity vector $v_t$ \emph{looks ahead}:"
            r" the next step starts from $x_t + v_t$, not from a"
            r" fresh gradient at $x_t$.",
            font_size=26,
            color=C_MOMENTUM,
        )
        annotation.to_corner(DOWN + LEFT).scale_to_fit_width(8.0)
        self.add_fixed_in_frame_mobjects(annotation)
        self.play(Write(annotation))
        self.next_slide()


class MomentumEquationDerivation(ContentSlide):
    """Derive momentum from GD: introduce v_t step by step."""

    header = "From GD to momentum, term by term"
    page_number = 8

    def construct(self) -> None:
        gd_eq = gd_equation(font_size=46)
        self.region.place(gd_eq, "center")
        gd_eq.shift(UP * 1.0)
        self.play(Write(gd_eq))
        self.next_slide()

        note_gd = BodyText(
            r"Standard GD: every step uses \emph{only} the gradient at $x_t$.",
        ).scale(0.75)
        note_gd.next_to(gd_eq, DOWN, buff=0.6)
        self.play(Write(note_gd))
        self.next_slide()

        # Replace eta * grad with eta * v_{t+1} and add the velocity update.
        self.play(FadeOut(note_gd))

        mo_eq = momentum_equation(font_size=40)
        self.region.place(mo_eq, "center")
        mo_eq.shift(UP * 0.4)
        self.play(ReplacementTransform(gd_eq, mo_eq))
        self.next_slide()

        # Caption boxes underneath instead of braces (avoids glyph collision).
        cap1 = BodyText(
            r"\textbf{(1)} A running average of past gradients $\rightarrow$ velocity.",
            color=C_MOMENTUM,
        ).scale(0.65)
        cap2 = BodyText(
            r"\textbf{(2)} Step along the velocity, not the raw gradient.",
            color=C_OPTIMUM,
        ).scale(0.65)
        captions = VGroup(cap1, cap2).arrange(DOWN, buff=0.3, aligned_edge=LEFT)
        captions.next_to(mo_eq, DOWN, buff=0.8)

        self.play(Write(cap1))
        self.next_slide()
        self.play(Write(cap2))
        self.next_slide()
