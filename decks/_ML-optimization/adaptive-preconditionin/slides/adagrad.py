"""AdaGrad slides: motivation, equation, behaviour.

The story arc:
    1.  AdaGradMotivation: contour plot showing per-coordinate gradients.
        Different coordinates pile up DIFFERENT total squared-gradient -- so
        each coordinate gets its OWN effective learning rate.

    2.  AdaGradEquation: build s_t, then x_{t+1} update.

    3.  AdaGradInAction: side-by-side GD vs AdaGrad on the same ill-conditioned
        bowl. AdaGrad converges in a straight line because it rescales axes.

    4.  AdaGradMirror: connect to mirror descent / Bregman divergence (notes §3.1).
"""

import numpy as np
from manim import (
    DOWN,
    LEFT,
    RIGHT,
    UP,
    Arrow,
    Brace,
    FadeIn,
    FadeOut,
    MathTex,
    Polygon,
    ReplacementTransform,
    SurroundingRectangle,
    VGroup,
    Write,
)

from simplex.engine.text import BodyText
from simplex.slides import ContentSlide

from common import (
    C_AXIS,
    C_GD,
    C_OPTIMUM,
    C_VARIANCE,
    EPS_ADAGRAD,
    OptState,
    adagrad_step,
    contour_quad,
    gd_step,
    glowing_dot,
    grad,
    gradient_arrow,
    make_2d_axes,
    run_optimizer,
    trail_from_points,
)


class AdaGradMotivation(ContentSlide):
    """Show that a single LR cannot fit all coordinates -- but the history can."""

    header = "AdaGrad: let history scale each coordinate"
    page_number = 9

    def construct(self) -> None:
        ax = make_2d_axes(
            x_range=(-2.6, 2.6, 1.0),
            y_range=(-2.6, 2.6, 1.0),
            width=5.2,
            height=5.2,
        )
        contours = contour_quad(ax, color=C_AXIS)
        panel = VGroup(ax, contours)
        self.region.place(panel, "left", buff=0.4)
        self.add(ax, contours)

        # Show 5 GD steps; at each, draw the gradient and highlight per-axis sizes.
        state = OptState(x=np.array([-2.0, 1.6]))
        positions = [state.x.copy()]
        grads = [grad(state.x[0], state.x[1])]
        for _ in range(5):
            gd_step(state, lr=0.18)
            positions.append(state.x.copy())
            grads.append(grad(state.x[0], state.x[1]))

        # Animate dots and gradient arrows step by step.
        dot = glowing_dot(ax.c2p(*positions[0]), color=C_GD)
        self.play(FadeIn(dot))

        # Right-side panel: an accumulator bar chart showing sum of squared grads.
        # We anchor the bars at a fixed BASELINE so growing upward never
        # collides with the title.
        bar_title = BodyText(r"Per-axis $s_t^2$").scale(0.6)

        baseline_y = -1.6
        x_bar_x = 4.2
        y_bar_x = 5.4
        bar_width = 0.4

        def make_bar(x_center: float, height: float, color: str) -> Polygon:
            return (
                Polygon(
                    np.array([x_center - bar_width / 2, baseline_y, 0.0]),
                    np.array([x_center + bar_width / 2, baseline_y, 0.0]),
                    np.array([x_center + bar_width / 2, baseline_y + height, 0.0]),
                    np.array([x_center - bar_width / 2, baseline_y + height, 0.0]),
                )
                .set_fill(color, opacity=0.85)
                .set_stroke(width=0)
            )

        x_bar = make_bar(x_bar_x, 0.12, C_GD)
        y_bar = make_bar(y_bar_x, 0.12, C_VARIANCE)
        x_label = MathTex(r"[s_t]_x^2", color=C_GD, font_size=24)
        x_label.move_to(np.array([x_bar_x, baseline_y - 0.3, 0.0]))
        y_label = MathTex(r"[s_t]_y^2", color=C_VARIANCE, font_size=24)
        y_label.move_to(np.array([y_bar_x, baseline_y - 0.3, 0.0]))

        bars = VGroup(x_bar, y_bar)
        labels = VGroup(x_label, y_label)
        bar_title.move_to(np.array([(x_bar_x + y_bar_x) / 2, 1.8, 0.0]))
        self.play(Write(bar_title))
        self.play(FadeIn(bars), FadeIn(labels))
        self.next_slide()

        # Run 5 GD steps; for each, grow the bars proportionally to grad^2.
        # Cap bar height so it cannot reach the title.
        max_height = 2.8
        accum = np.array([EPS_ADAGRAD, EPS_ADAGRAD])
        trails: list[Arrow] = []
        for i in range(5):
            g = grads[i]
            arrow = gradient_arrow(
                ax,
                positions[i],
                g,
                color=C_GD,
                scale=0.18,
                stroke_width=4,
            )
            trails.append(arrow)
            accum = accum + g * g
            new_h_x = min(max_height, float(np.sqrt(accum[0])) * 0.6)
            new_h_y = min(max_height, float(np.sqrt(accum[1])) * 0.6)
            new_x_bar = make_bar(x_bar_x, new_h_x, C_GD)
            new_y_bar = make_bar(y_bar_x, new_h_y, C_VARIANCE)
            self.play(
                FadeIn(arrow, run_time=0.35),
                dot.animate.move_to(ax.c2p(*positions[i + 1])),
                ReplacementTransform(x_bar, new_x_bar, run_time=0.35),
                ReplacementTransform(y_bar, new_y_bar, run_time=0.35),
            )
            x_bar = new_x_bar
            y_bar = new_y_bar
        self.next_slide()

        # Caption: the steep x accumulates faster than y, so x's LR shrinks faster.
        moral = (
            VGroup(
                BodyText(r"Steep coordinate $\Rightarrow$ huge accumulator $\Rightarrow$"),
                BodyText(r"AdaGrad \emph{shrinks} its step on that axis."),
            )
            .arrange(DOWN, buff=0.1)
            .scale(0.65)
        )
        for line in moral:
            line.set_color(C_OPTIMUM)
        self.region.place(moral, "bottom", buff=0.15)
        self.play(Write(moral))
        self.next_slide()


class AdaGradEquation(ContentSlide):
    """Build s_t, then the AdaGrad update rule, with colored annotations."""

    header = "AdaGrad: the equations"
    page_number = 10

    def construct(self) -> None:
        # Step 1: introduce s_t.
        intro = BodyText(r"AdaGrad keeps a per-coordinate accumulator of squared gradients:").scale(
            0.75
        )
        self.region.place(intro, "top", buff=0.4)
        self.play(Write(intro))
        self.next_slide()

        # Step 2: show s_t equation.
        eq_s = MathTex(
            r"[s_t]_i",
            r"=",
            r"\sqrt{\sum_{\tau=0}^{t}\,",
            r"[\nabla f(x_\tau)]_i^{\,2}",
            r"}",
            font_size=44,
        )
        eq_s[0].set_color(C_VARIANCE)
        eq_s[2].set_color(C_VARIANCE)
        eq_s[3].set_color(C_GD)
        eq_s[4].set_color(C_VARIANCE)
        eq_s.next_to(intro, DOWN, buff=0.6)
        self.play(Write(eq_s))
        self.next_slide()

        # Annotate s_t with a brace + manually-positioned caption.
        brace = Brace(eq_s, direction=DOWN, buff=0.15, color=C_VARIANCE)
        brace_caption = BodyText(
            r"\textit{Larger past gradients} $\Rightarrow$"
            r" \textit{larger} $[s_t]_i$.",
            color=C_VARIANCE,
        ).scale(0.55)
        brace_caption.next_to(brace, DOWN, buff=0.15)
        brace_group = VGroup(brace, brace_caption)
        self.play(Write(brace_group))
        self.next_slide()

        # Step 3: the AdaGrad update rule.
        self.play(FadeOut(brace_group), FadeOut(intro))

        eq_x = MathTex(
            r"x_{t+1}",
            r"=",
            r"x_t",
            r"-",
            r"\eta",
            r"\,M_t^{-1}\,",
            r"\nabla f(x_t)",
            font_size=44,
        )
        eq_x[4].set_color(C_OPTIMUM)
        eq_x[5].set_color(C_VARIANCE)
        eq_x[6].set_color(C_GD)
        eq_x.next_to(eq_s, DOWN, buff=0.9)
        self.play(Write(eq_x))
        self.next_slide()

        # M_t = diag(s_t)
        defn = MathTex(
            r"M_t",
            r"=",
            r"\mathrm{diag}([s_t]_1, \dots, [s_t]_n)",
            font_size=28,
        )
        defn[0].set_color(C_VARIANCE)
        defn[2].set_color(C_VARIANCE)
        defn.next_to(eq_x, DOWN, buff=0.4)
        self.play(Write(defn))
        self.next_slide()

        # Highlight that M_t^{-1} is a per-axis scaling -- box at bottom.
        callout = BodyText(
            r"Effective LR on axis $i$ becomes $\eta / [s_t]_i$ -- small for steep axes.",
            color=C_OPTIMUM,
        ).scale(0.55)
        self.region.place(callout, "bottom", buff=0.2)
        self.play(Write(callout))
        self.next_slide()


class AdaGradInAction(ContentSlide):
    """Race: vanilla GD vs AdaGrad on the same ill-conditioned bowl."""

    header = "AdaGrad in action"
    page_number = 11

    def construct(self) -> None:
        ax = make_2d_axes(width=8.5, height=5.0)
        contours = contour_quad(ax, color=C_AXIS)
        self.region.place(VGroup(ax, contours), "center")
        self.add(ax, contours)

        opt_marker = glowing_dot(ax.c2p(0, 0), color=C_OPTIMUM, radius=0.09, glow_scale=2.2)
        self.play(FadeIn(opt_marker))
        self.next_slide()

        # Run both trajectories.
        gd_pts = run_optimizer(lambda s: gd_step(s, lr=0.42), n_steps=22)
        ada_pts = run_optimizer(lambda s: adagrad_step(s, lr=1.4), n_steps=22)

        gd_trail = trail_from_points(ax, gd_pts, color=C_GD)
        ada_trail = trail_from_points(ax, ada_pts, color=C_VARIANCE)

        legend = VGroup(
            BodyText(r"\textbf{GD} (fixed LR)", color=C_GD).scale(0.6),
            BodyText(r"\textbf{AdaGrad}", color=C_VARIANCE).scale(0.6),
        ).arrange(DOWN, buff=0.15, aligned_edge=LEFT)
        legend.to_corner(UP + LEFT).shift(DOWN * 0.6 + RIGHT * 0.4)
        self.play(Write(legend))
        self.next_slide()

        gd_head = glowing_dot(ax.c2p(*gd_pts[-1]), color=C_GD)
        ada_head = glowing_dot(ax.c2p(*ada_pts[-1]), color=C_VARIANCE)
        self.play(Write(gd_trail), FadeIn(gd_head, run_time=0.4), run_time=2.0)
        self.next_slide()
        self.play(Write(ada_trail), FadeIn(ada_head, run_time=0.4), run_time=2.0)
        self.next_slide()

        moral = BodyText(
            r"AdaGrad walks (almost) straight to the optimum --"
            r" because it has \emph{rescaled} the axes.",
            color=C_OPTIMUM,
        ).scale(0.7)
        moral.scale_to_fit_width(self.region.width * 0.75)
        self.region.place(moral, "bottom", buff=0.2)
        self.play(Write(moral))
        self.next_slide()


class AdaGradMirror(ContentSlide):
    """AdaGrad = mirror descent with a time-varying quadratic d.g.f.

    From notes §3.1:
        phi_t(x) = 1/2 * x^T M_t x
        D_phi_t(x || y) = 1/2 (x-y)^T M_t (x-y)
        argmin_x { eta * <grad f(x_t), x> + D_phi_t(x || x_t) }
            -> x_{t+1} = x_t - eta * M_t^{-1} * grad f(x_t)
    """

    header = "AdaGrad is mirror descent in disguise"
    page_number = 12

    def construct(self) -> None:
        intro = BodyText(
            r"Pick a \emph{time-varying} distance-generating function:",
        ).scale(0.85)
        self.region.place(intro, "top", buff=0.4)
        self.play(Write(intro))
        self.next_slide()

        phi_eq = MathTex(
            r"\varphi_t(x)",
            r"=",
            r"\tfrac{1}{2}\, x^\top",
            r"M_t",
            r"\, x",
            font_size=40,
        )
        phi_eq[3].set_color(C_VARIANCE)
        phi_eq.next_to(intro, DOWN, buff=0.45)
        self.play(Write(phi_eq))
        self.next_slide()

        # Induced Bregman divergence.
        bregman = MathTex(
            r"\mathrm{D}_{\varphi_t}(x\,\|\,y)",
            r"=",
            r"\tfrac{1}{2}\, (x-y)^\top",
            r"M_t",
            r"(x-y)",
            font_size=38,
        )
        bregman[0].set_color(C_VARIANCE)
        bregman[3].set_color(C_VARIANCE)
        bregman.next_to(phi_eq, DOWN, buff=0.45)
        self.play(Write(bregman))
        self.next_slide()

        # The mirror descent update.
        md = MathTex(
            r"x_{t+1}",
            r"=",
            r"\arg\min_{x}\,",
            r"\bigl\{\,\eta\,\langle\nabla f(x_t),\, x\rangle",
            r"+",
            r"\mathrm{D}_{\varphi_t}(x\,\|\,x_t)",
            r"\bigr\}",
            font_size=34,
        )
        md[3].set_color(C_GD)
        md[5].set_color(C_VARIANCE)
        md.next_to(bregman, DOWN, buff=0.55)
        self.play(Write(md))
        self.next_slide()

        # Setting derivative to zero gives back AdaGrad.
        arrow = Arrow(
            start=md.get_bottom() + DOWN * 0.05,
            end=md.get_bottom() + DOWN * 0.55,
            buff=0.1,
            color=C_OPTIMUM,
        )
        result = MathTex(
            r"x_{t+1}",
            r"=",
            r"x_t",
            r"-",
            r"\eta\,",
            r"M_t^{-1}",
            r"\nabla f(x_t)",
            font_size=38,
        )
        result[4].set_color(C_OPTIMUM)
        result[5].set_color(C_VARIANCE)
        result[6].set_color(C_GD)
        result.next_to(arrow, DOWN, buff=0.15)

        # Box around the rediscovered AdaGrad rule.
        box = SurroundingRectangle(result, color=C_OPTIMUM, corner_radius=0.12, buff=0.18)

        self.play(Write(arrow))
        self.play(Write(result))
        self.play(Write(box))
        self.next_slide()
