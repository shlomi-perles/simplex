"""ADAM slides: derive ADAM as AdaGrad + Momentum.

The narrative:
    1.  AdamBuildUp: side-by-side momentum (green) and AdaGrad (blue)
        equations. Show them sliding together into a unified ADAM scheme.
    2.  AdamEquations: full three-line ADAM update rule.
    3.  AdamBoxes: highlight which knob does what (gamma, beta, eta).
    4.  AdamRace: side-by-side trajectories of GD, momentum, AdaGrad, ADAM.
"""

from manim import (
    DOWN,
    LEFT,
    RIGHT,
    UP,
    CurvedArrow,
    MathTex,
    SurroundingRectangle,
    VGroup,
    Write,
)

from simplex.engine.text import BodyText, Caption
from simplex.slides import ContentSlide

from common import (  # noqa: I001
    C_ADAM,
    C_GD,
    C_MOMENTUM,
    C_OPTIMUM,
    C_VARIANCE,
)
from equation_lab import adam_equations


class AdamBuildUp(ContentSlide):
    """Show that ADAM = Momentum (first moment) + AdaGrad (second moment)."""

    header = "ADAM = Momentum + AdaGrad (with a discount)"
    page_number = 13

    def construct(self) -> None:
        # Left panel: momentum equation.
        mom_eq = MathTex(
            r"g_t",
            r"=",
            r"\gamma\, g_{t-1}",
            r"+",
            r"(1-\gamma)\,",
            r"\nabla f(x_t)",
            font_size=32,
        )
        mom_eq[0].set_color(C_MOMENTUM)
        mom_eq[2].set_color(C_MOMENTUM)
        mom_eq[5].set_color(C_GD)

        # Right panel: AdaGrad accumulator with a discount (RMSProp form).
        var_eq = MathTex(
            r"[s_t]_i^{\,2}",
            r"=",
            r"\beta\,[s_{t-1}]_i^{\,2}",
            r"+",
            r"(1-\beta)\,",
            r"[\nabla f(x_t)]_i^{\,2}",
            font_size=32,
        )
        var_eq[0].set_color(C_VARIANCE)
        var_eq[2].set_color(C_VARIANCE)
        var_eq[5].set_color(C_GD)

        left_caption = Caption(r"Momentum (first moment)", color=C_MOMENTUM)
        right_caption = Caption(r"AdaGrad-style (second moment)", color=C_VARIANCE)

        left_panel = VGroup(left_caption, mom_eq).arrange(DOWN, buff=0.4)
        right_panel = VGroup(right_caption, var_eq).arrange(DOWN, buff=0.4)
        panels = VGroup(left_panel, right_panel).arrange(RIGHT, buff=1.2)
        self.region.place(panels, "center")
        panels.shift(UP * 0.6)
        self.play(Write(left_panel))
        self.play(Write(right_panel))
        self.next_slide()

        # Combine: x_{t+1} = x_t - eta * M_t^{-1} * g_t.
        combine = MathTex(
            r"x_{t+1}",
            r"=",
            r"x_t",
            r"-",
            r"\eta\,",
            r"M_t^{-1}",
            r"g_t",
            font_size=44,
        )
        combine[4].set_color(C_OPTIMUM)
        combine[5].set_color(C_VARIANCE)
        combine[6].set_color(C_MOMENTUM)
        combine.next_to(panels, DOWN, buff=0.9)

        # Build a "merging" visual: arrows from each side curving into combine.
        l_arrow = CurvedArrow(
            start_point=mom_eq.get_bottom() + DOWN * 0.05,
            end_point=combine[6].get_top() + UP * 0.05,
            angle=-0.6,
            color=C_MOMENTUM,
        )
        r_arrow = CurvedArrow(
            start_point=var_eq.get_bottom() + DOWN * 0.05,
            end_point=combine[5].get_top() + UP * 0.05,
            angle=0.6,
            color=C_VARIANCE,
        )
        self.play(Write(l_arrow), Write(r_arrow))
        self.play(Write(combine))
        self.next_slide()

        # Highlight + caption.
        box = SurroundingRectangle(combine, color=C_ADAM, corner_radius=0.12, buff=0.18)
        self.play(Write(box))
        self.next_slide()


class AdamEquations(ContentSlide):
    """Final ADAM equations: three lines with colored decomposition."""

    header = "ADAM in full"
    page_number = 14

    def construct(self) -> None:
        eqs = adam_equations(font_size=40)
        self.region.place(eqs, "center")
        eqs.shift(UP * 0.4)
        self.play(Write(eqs[0]))
        self.next_slide()
        self.play(Write(eqs[1]))
        self.next_slide()
        self.play(Write(eqs[2]))
        self.next_slide()

        # Hyperparam defaults from notes (PyTorch defaults).
        eta_part = MathTex(r"\eta = 0.001", font_size=30, color=C_OPTIMUM)
        gamma_part = MathTex(r"\gamma = 0.9", font_size=30, color=C_MOMENTUM)
        beta_part = MathTex(r"\beta = 0.999", font_size=30, color=C_VARIANCE)
        hp = VGroup(
            BodyText(r"PyTorch defaults:").scale(0.7),
            VGroup(eta_part, gamma_part, beta_part).arrange(RIGHT, buff=0.7),
        ).arrange(DOWN, buff=0.25)
        hp.next_to(eqs, DOWN, buff=0.7)
        self.play(Write(hp))
        self.next_slide()


class AdamBoxes(ContentSlide):
    """Highlight each knob's role in the update rule with brackets."""

    header = "What each knob does"
    page_number = 15

    def construct(self) -> None:
        eqs = adam_equations(font_size=40)
        self.region.place(eqs, "center")
        eqs.shift(UP * 0.4)
        self.add(eqs)
        self.next_slide()

        # Highlight gamma (momentum decay) -> highlight beta (variance decay) ->
        # highlight eta (overall step).
        gamma_box = SurroundingRectangle(
            eqs[0][2],
            color=C_MOMENTUM,
            buff=0.06,
            corner_radius=0.05,
        )
        beta_box = SurroundingRectangle(
            eqs[1][2],
            color=C_VARIANCE,
            buff=0.06,
            corner_radius=0.05,
        )
        eta_box = SurroundingRectangle(
            eqs[2][4],
            color=C_OPTIMUM,
            buff=0.06,
            corner_radius=0.05,
        )

        gamma_note = BodyText(
            r"$\gamma$: how much the velocity \emph{remembers}.",
            color=C_MOMENTUM,
        ).scale(0.7)
        beta_note = BodyText(
            r"$\beta$: how slowly the accumulator \emph{forgets}.",
            color=C_VARIANCE,
        ).scale(0.7)
        eta_note = BodyText(
            r"$\eta$: the global step scale.",
            color=C_OPTIMUM,
        ).scale(0.7)

        gamma_note.next_to(eqs, DOWN, buff=0.45).align_to(eqs, LEFT)
        beta_note.next_to(gamma_note, DOWN, buff=0.18).align_to(eqs, LEFT)
        eta_note.next_to(beta_note, DOWN, buff=0.18).align_to(eqs, LEFT)

        self.play(Write(gamma_box), Write(gamma_note))
        self.next_slide()
        self.play(Write(beta_box), Write(beta_note))
        self.next_slide()
        self.play(Write(eta_box), Write(eta_note))
        self.next_slide()


class AdamCaveat(ContentSlide):
    """Acknowledge the divergence caveat from notes (RKK18)."""

    header = "ADAM in practice"
    page_number = 16

    def construct(self) -> None:
        bullets = VGroup(
            BodyText(
                r"\textbf{In practice.} ADAM is the default optimizer for"
                r" deep learning.",
            ),
            BodyText(
                r"\textbf{Theory.} Unlike AdaGrad, ADAM has \emph{no}"
                r" convergence guarantee in general.",
            ),
            BodyText(
                r"\textbf{Caveat.} ADAM can \emph{diverge} even on convex"
                r" objectives [Reddi et al., 2018].",
                color=C_GD,
            ),
            BodyText(
                r"$\Rightarrow$ Variants such as AMSGrad fix this.",
                color=C_OPTIMUM,
            ),
        ).arrange(DOWN, buff=0.45, aligned_edge=LEFT)
        bullets.scale_to_fit_width(self.region.width * 0.8)
        self.region.place(bullets, "center")
        for line in bullets:
            self.play(Write(line))
            self.next_slide()
