"""Equation-construction helpers tailored to optimizer formulas.

The whole deck builds up four equations:
    GD:        x_{t+1} = x_t - eta * grad
    Momentum:  v_{t+1} = gamma * v_t + (1-gamma) * grad
               x_{t+1} = x_t - eta * v_{t+1}
    AdaGrad:   s_t = sqrt(sum grad^2)
               x_{t+1} = x_t - eta * grad / s_t
    ADAM:      m_t = gamma * m_{t-1} + (1-gamma) * grad
               s_t^2 = beta * s_{t-1}^2 + (1-beta) * grad^2
               x_{t+1} = x_t - eta * m_t / s_t

Build them with shared glyph keys so TransformMatchingTex can morph between
forms cleanly.
"""

from manim import (
    DOWN,
    LEFT,
    MathTex,
    VGroup,
)

from common import C_GD, C_MOMENTUM, C_OPTIMUM, C_VARIANCE  # noqa: I001


def gd_equation(font_size: int = 44) -> MathTex:
    eq = MathTex(
        r"x_{t+1}",
        r"=",
        r"x_t",
        r"-",
        r"\eta",
        r"\nabla f(x_t)",
        font_size=font_size,
    )
    eq[5].set_color(C_GD)
    eq[4].set_color(C_OPTIMUM)
    return eq


def momentum_equation(font_size: int = 40) -> VGroup:
    line1 = MathTex(
        r"v_{t+1}",
        r"=",
        r"\gamma\, v_t",
        r"+",
        r"(1-\gamma)\,",
        r"\nabla f(x_t)",
        font_size=font_size,
    )
    line1[0].set_color(C_MOMENTUM)
    line1[2].set_color(C_MOMENTUM)
    line1[5].set_color(C_GD)

    line2 = MathTex(
        r"x_{t+1}",
        r"=",
        r"x_t",
        r"-",
        r"\eta\,",
        r"v_{t+1}",
        font_size=font_size,
    )
    line2[4].set_color(C_OPTIMUM)
    line2[5].set_color(C_MOMENTUM)

    out = VGroup(line1, line2).arrange(DOWN, buff=0.35, aligned_edge=LEFT)
    return out


def adagrad_equation(font_size: int = 40) -> VGroup:
    accumulator = MathTex(
        r"[s_t]_i",
        r"=",
        r"\sqrt{\sum_{\tau=0}^t [\nabla f(x_\tau)]_i^{\,2}}",
        font_size=font_size,
    )
    accumulator[0].set_color(C_VARIANCE)
    accumulator[2].set_color(C_VARIANCE)

    update = MathTex(
        r"x_{t+1}",
        r"=",
        r"x_t",
        r"-",
        r"\eta\,",
        r"M_t^{-1}",
        r"\nabla f(x_t)",
        font_size=font_size,
    )
    update[4].set_color(C_OPTIMUM)
    update[5].set_color(C_VARIANCE)
    update[6].set_color(C_GD)

    out = VGroup(accumulator, update).arrange(DOWN, buff=0.45, aligned_edge=LEFT)
    return out


def adam_equations(font_size: int = 36) -> VGroup:
    m_line = MathTex(
        r"g_t",
        r"=",
        r"\gamma\, g_{t-1}",
        r"+",
        r"(1-\gamma)\,",
        r"\nabla f(x_t)",
        font_size=font_size,
    )
    m_line[0].set_color(C_MOMENTUM)
    m_line[2].set_color(C_MOMENTUM)
    m_line[5].set_color(C_GD)

    s_line = MathTex(
        r"[s_t]_i^{\,2}",
        r"=",
        r"\beta\, [s_{t-1}]_i^{\,2}",
        r"+",
        r"(1-\beta)\,",
        r"[\nabla f(x_t)]_i^{\,2}",
        font_size=font_size,
    )
    s_line[0].set_color(C_VARIANCE)
    s_line[2].set_color(C_VARIANCE)
    s_line[5].set_color(C_GD)

    x_line = MathTex(
        r"x_{t+1}",
        r"=",
        r"x_t",
        r"-",
        r"\eta\,",
        r"M_t^{-1}",
        r"g_t",
        font_size=font_size,
    )
    x_line[4].set_color(C_OPTIMUM)
    x_line[5].set_color(C_VARIANCE)
    x_line[6].set_color(C_MOMENTUM)

    out = VGroup(m_line, s_line, x_line).arrange(DOWN, buff=0.32, aligned_edge=LEFT)
    return out


def kicker_equation(font_size: int = 48) -> MathTex:
    """The unified `x_{t+1} = x_t - eta * M_t^{-1} * g_t` formula.

    Re-used as the intro preview, the Recap kicker, and as a recurring
    "north star" throughout the deck.
    """
    eq = MathTex(
        r"x_{t+1}", r"=", r"x_t", r"-",
        r"\eta\,", r"M_t^{-1}", r"g_t",
        font_size=font_size,
    )
    eq[4].set_color(C_OPTIMUM)
    eq[5].set_color(C_VARIANCE)
    eq[6].set_color(C_MOMENTUM)
    return eq


__all__ = [
    "adagrad_equation",
    "adam_equations",
    "gd_equation",
    "kicker_equation",
    "momentum_equation",
]
