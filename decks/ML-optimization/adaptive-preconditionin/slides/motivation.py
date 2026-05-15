"""Motivation slides: why preconditioning, and what GD gets wrong on
ill-conditioned problems.

We follow the notes' meters-vs-centimeters story:
    f(x, y) = 1/2 x^2 + 1/2 y^2
    g(x', y) = f(x'/sqrt(2), y) = 1/4 x'^2 + 1/2 y^2

By zooming the x-axis, gradient descent slows down dramatically along x.
We animate two contour fields side-by-side and let two dots run with the
*same* learning rate; the right one (rescaled coordinates) zigzags slowly.
"""

from manim import (
    DOWN,
    LEFT,
    RIGHT,
    UP,
    FadeIn,
    VGroup,
    Write,
)

from simplex.engine.text import BodyText, Caption
from simplex.slides import ContentSlide

# Local helpers (slides dir is on sys.path inside the running script).
from common import (  # noqa: I001
    A_X,
    A_Y,
    C_AXIS,
    C_GD,
    C_MOMENTUM,
    C_OPTIMUM,
    C_VARIANCE,
    contour_quad,
    glowing_dot,
    gradient_arrow,
    make_2d_axes,
    trail_from_points,
    gd_step,
    run_optimizer,
)


class WhyPreconditioning(ContentSlide):
    """Three-beat motivation: physical units -> reparam scale -> GD zigzags."""

    header = "Why adaptive learning rates?"
    page_number = 2

    def construct(self) -> None:
        bullets = VGroup(
            BodyText(r"\textbf{1.} GD treats every coordinate \emph{identically}.").scale(0.85),
            BodyText(r"\textbf{2.} Coordinates live on \emph{different scales}.").scale(0.85),
            BodyText(r"\textbf{3.} A change of units alone can wreck convergence.").scale(0.85),
            BodyText(
                r"\textbf{$\Rightarrow$} We need \emph{per-coordinate} LRs.",
                color=C_OPTIMUM,
            ).scale(0.85),
        ).arrange(DOWN, buff=0.5, aligned_edge=LEFT)
        self.region.place(bullets, "center")

        for line in bullets:
            self.play(Write(line))
            self.next_slide()


class UnitsExample(ContentSlide):
    """The notes' analytical example: f vs g side-by-side."""

    header = "A unit change becomes an ill-conditioning"
    page_number = 3

    def construct(self) -> None:
        left_caption = Caption(
            r"$f(x, y) = \tfrac{1}{2}x^2 + \tfrac{1}{2}y^2$",
            color=C_MOMENTUM,
        )
        right_caption = Caption(
            r"$g(x', y) = \tfrac{1}{20}x'^2 + \tfrac{1}{2}y^2$",
            color=C_VARIANCE,
        )

        ax_left = make_2d_axes(width=4.6, height=4.0)
        ax_right = make_2d_axes(width=4.6, height=4.0)

        # Round / isotropic contours on the left (kept small).
        contours_left = contour_quad(
            ax_left, a_x=1.0, a_y=1.0, color=C_MOMENTUM, opacity=0.7,
            levels=(0.4, 1.0, 2.0, 3.5),
        )
        # Elongated contours on the right (0.1, 1 -> very stretched).
        contours_right = contour_quad(
            ax_right, a_x=0.1, a_y=1.0, color=C_VARIANCE, opacity=0.7,
            levels=(0.5, 1.3, 2.4),
        )

        group_left = VGroup(ax_left, contours_left)
        group_right = VGroup(ax_right, contours_right)
        panels = VGroup(group_left, group_right).arrange(RIGHT, buff=0.6)
        panels.scale_to_fit_width(self.region.width * 0.95)
        self.region.place(panels, "center")
        panels.shift(DOWN * 0.2)

        left_caption.next_to(group_left, UP, buff=0.25)
        right_caption.next_to(group_right, UP, buff=0.25)

        self.play(FadeIn(ax_left), FadeIn(ax_right))
        self.play(Write(left_caption), Write(right_caption))
        self.play(FadeIn(contours_left, lag_ratio=0.1), FadeIn(contours_right, lag_ratio=0.1))
        self.next_slide()

        # Same starting point in both views.
        start = (-1.6, 1.2)
        dot_l = glowing_dot(ax_left.c2p(*start), color=C_GD)
        dot_r = glowing_dot(ax_right.c2p(*start), color=C_GD)

        # Per-panel curvature -> per-panel gradient direction.
        grad_l = gradient_arrow(
            ax_left, point=start, grad_vec=(1.0 * start[0], 1.0 * start[1]),
            color=C_GD, scale=0.6, stroke_width=7,
        )
        grad_r = gradient_arrow(
            ax_right, point=start, grad_vec=(0.1 * start[0], 1.0 * start[1]),
            color=C_GD, scale=0.6, stroke_width=7,
        )
        self.play(FadeIn(dot_l), FadeIn(dot_r))
        self.play(Write(grad_l), Write(grad_r))
        self.next_slide()

        # Caption explaining what just happened.
        moral = BodyText(
            r"Same point, same algorithm, different units"
            r" $\Rightarrow$ \emph{different} descent direction."
        )
        moral.scale_to_fit_width(self.region.width * 0.75)
        moral.next_to(panels, DOWN, buff=0.3)
        self.play(Write(moral))
        self.next_slide()


class GDZigzag(ContentSlide):
    """Final motivation: show the zigzag of GD on the ill-conditioned bowl."""

    header = "Vanilla GD zigzags on stretched bowls"
    page_number = 4

    def construct(self) -> None:
        ax = make_2d_axes(width=8.0, height=5.0)
        contours = contour_quad(ax, a_x=A_X, a_y=A_Y, color=C_AXIS)
        self.region.place(VGroup(ax, contours), "center")

        legend_lr = BodyText(
            r"\textbf{LR too small} $\Rightarrow$ slow",
            color=C_VARIANCE,
        ).scale(0.55)
        legend_zz = BodyText(
            r"\textbf{LR too large} $\Rightarrow$ zigzag / divergence",
            color=C_GD,
        ).scale(0.55)
        legend = VGroup(legend_lr, legend_zz).arrange(DOWN, buff=0.15, aligned_edge=LEFT)
        legend.to_corner(UP + LEFT, buff=0.6).shift(DOWN * 0.6)
        self.add(ax, contours, legend)
        self.next_slide()

        # Build two trajectories from the *same* start, different LRs.
        small_pts = run_optimizer(lambda s: gd_step(s, lr=0.03), n_steps=22)
        big_pts = run_optimizer(lambda s: gd_step(s, lr=0.42), n_steps=22)
        small_trail = trail_from_points(ax, small_pts, color=C_VARIANCE)
        big_trail = trail_from_points(ax, big_pts, color=C_GD)
        small_head = glowing_dot(ax.c2p(*small_pts[-1]), color=C_VARIANCE)
        big_head = glowing_dot(ax.c2p(*big_pts[-1]), color=C_GD)

        opt_marker = glowing_dot(ax.c2p(0.0, 0.0), color=C_OPTIMUM, radius=0.09, glow_scale=2.2)
        self.play(FadeIn(opt_marker))
        self.next_slide()

        self.play(Write(small_trail), FadeIn(small_head, run_time=0.4), run_time=2.2)
        self.next_slide()

        self.play(Write(big_trail), FadeIn(big_head, run_time=0.4), run_time=2.2)
        self.next_slide()

        moral = BodyText(
            r"GD does not know which axis is steep --"
            r" but the \emph{history of gradients} does."
        )
        moral.scale_to_fit_width(self.region.width * 0.75)
        self.region.place(moral, "bottom", buff=0.3)
        self.play(Write(moral))
        self.next_slide()
