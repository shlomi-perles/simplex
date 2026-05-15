"""Shared style, palette, and helpers for the adaptive-preconditioning deck.

Centralizes:
- Color constants (semantic: momentum = green, variance = blue, gradient = red).
- Geometric constants (axes range, learning rates, surface shape).
- Optimizer step functions that take a state and return the next state.
- Common mobject builders (glowing dots, trajectory poly-lines, equation badges).

Keep this file small enough that individual slide modules stay declarative.
"""

from collections.abc import Callable
from dataclasses import dataclass, field

import numpy as np
from manim import (
    BLUE,
    GREEN,
    GREY_B,
    GREY_D,
    RED,
    YELLOW,
    Arrow,
    Axes,
    Circle,
    Dot,
    Surface,
    ThreeDAxes,
    VGroup,
    VMobject,
)

# ----------------------------------------------------------------------
# Semantic palette -- the colors keep their meaning across all slides
# so the student builds a stable visual vocabulary.
# ----------------------------------------------------------------------
C_GD = "#FF4F6A"  # vanilla gradient descent / current gradient
C_MOMENTUM = "#38D996"  # momentum / first moment m_t / look-ahead vector
C_VARIANCE = "#5BC8FF"  # AdaGrad accumulator s_t / second moment v_t
C_ADAM = "#FFD93D"  # combined ADAM trajectory
C_OPTIMUM = "#FFD93D"  # x_star marker
C_AXIS = "#9CA3AF"  # axis lines + grid

# Translucent / muted variants for trails and context
C_TRAIL = "#F7B7C0"
C_DIM = GREY_B

# ----------------------------------------------------------------------
# Step-size + iteration constants
# ----------------------------------------------------------------------
LR_GD = 0.18
LR_MOMENTUM = 0.18
GAMMA_MOMENTUM = 0.85
LR_ADAGRAD = 1.2
EPS_ADAGRAD = 1e-8
LR_ADAM = 0.45
GAMMA_ADAM = 0.9
BETA_ADAM = 0.999
EPS_ADAM = 1e-8
N_STEPS = 28

# ----------------------------------------------------------------------
# Loss landscape (used in both 2D contour and 3D surface)
# Ill-conditioned quadratic mimicking the "meters vs. centimeters" example
# from the notes: x-axis is 10x more curved than y-axis.
# ----------------------------------------------------------------------
A_X = 4.0  # curvature along x
A_Y = 0.4  # curvature along y -- much flatter -> "ill conditioned"
START_POINT = np.array([-2.2, 2.0])


def loss(x: float, y: float) -> float:
    return 0.5 * A_X * x * x + 0.5 * A_Y * y * y


def grad(x: float, y: float) -> np.ndarray:
    return np.array([A_X * x, A_Y * y])


# ----------------------------------------------------------------------
# Optimizer states + step functions. Each `step` mutates and returns the
# updated state so a scene can keep a clean loop.
# ----------------------------------------------------------------------
@dataclass
class OptState:
    x: np.ndarray
    velocity: np.ndarray = field(default_factory=lambda: np.zeros(2))
    accum_sq: np.ndarray = field(default_factory=lambda: np.zeros(2))
    moment1: np.ndarray = field(default_factory=lambda: np.zeros(2))
    moment2: np.ndarray = field(default_factory=lambda: np.zeros(2))
    t: int = 0


def gd_step(state: OptState, lr: float = LR_GD) -> OptState:
    g = grad(state.x[0], state.x[1])
    state.x = state.x - lr * g
    state.t += 1
    return state


def momentum_step(
    state: OptState,
    lr: float = LR_MOMENTUM,
    gamma: float = GAMMA_MOMENTUM,
) -> OptState:
    g = grad(state.x[0], state.x[1])
    state.velocity = gamma * state.velocity + (1.0 - gamma) * g
    state.x = state.x - lr * state.velocity
    state.t += 1
    return state


def adagrad_step(state: OptState, lr: float = LR_ADAGRAD) -> OptState:
    g = grad(state.x[0], state.x[1])
    state.accum_sq = state.accum_sq + g * g
    state.x = state.x - lr * g / (np.sqrt(state.accum_sq) + EPS_ADAGRAD)
    state.t += 1
    return state


def adam_step(
    state: OptState,
    lr: float = LR_ADAM,
    gamma: float = GAMMA_ADAM,
    beta: float = BETA_ADAM,
) -> OptState:
    g = grad(state.x[0], state.x[1])
    state.moment1 = gamma * state.moment1 + (1.0 - gamma) * g
    state.moment2 = beta * state.moment2 + (1.0 - beta) * g * g
    state.x = state.x - lr * state.moment1 / (np.sqrt(state.moment2) + EPS_ADAM)
    state.t += 1
    return state


def run_optimizer(
    step_fn: Callable[[OptState], OptState],
    *,
    start: np.ndarray = START_POINT,
    n_steps: int = N_STEPS,
) -> np.ndarray:
    """Return an (n_steps+1, 2) array of iterates."""
    state = OptState(x=start.copy())
    pts = [state.x.copy()]
    for _ in range(n_steps):
        step_fn(state)
        pts.append(state.x.copy())
    return np.asarray(pts)


# ----------------------------------------------------------------------
# Visual helpers
# ----------------------------------------------------------------------
def glowing_dot(
    position: np.ndarray,
    *,
    color: str,
    radius: float = 0.11,
    glow_scale: float = 2.6,
    glow_opacity: float = 0.3,
) -> VGroup:
    """A small dot wrapped in a translucent glow halo (Repo 2 trick)."""
    core = Dot(position, color=color, radius=radius)
    halo = Circle(radius=radius * glow_scale, color=color)
    halo.set_fill(color=color, opacity=glow_opacity).set_stroke(width=0)
    halo.move_to(position)
    g = VGroup(halo, core)
    g.core = core  # type: ignore[attr-defined]
    g.halo = halo  # type: ignore[attr-defined]
    return g


def trail_from_points(
    axes: Axes,
    pts: np.ndarray,
    *,
    color: str,
    stroke_width: float = 4.0,
    opacity: float = 0.85,
) -> VMobject:
    """Build a polyline trajectory in axes coordinates."""
    line = VMobject(color=color, stroke_width=stroke_width)
    coords = [axes.c2p(float(p[0]), float(p[1])) for p in pts]
    line.set_points_as_corners(coords)
    line.set_stroke(color=color, width=stroke_width, opacity=opacity)
    return line


def contour_quad(
    axes: Axes,
    *,
    a_x: float = A_X,
    a_y: float = A_Y,
    levels: tuple[float, ...] = (0.4, 1.2, 2.4, 4.0, 6.5, 10.0, 15.0),
    color: str = C_AXIS,
    opacity: float = 0.55,
) -> VGroup:
    """Filled / stroked elliptic contour lines for a quadratic loss."""
    from manim import ParametricFunction

    out = VGroup()
    for level in levels:
        rx = float(np.sqrt(2 * level / a_x))
        ry = float(np.sqrt(2 * level / a_y))
        ellipse = ParametricFunction(
            lambda t, rx=rx, ry=ry: axes.c2p(rx * np.cos(t), ry * np.sin(t)),
            t_range=(0.0, 2.0 * np.pi),
            color=color,
            stroke_width=1.6,
        )
        ellipse.set_stroke(opacity=opacity)
        out.add(ellipse)
    return out


def gradient_arrow(
    axes: Axes,
    point: np.ndarray,
    grad_vec: np.ndarray,
    *,
    color: str = C_GD,
    scale: float = 0.18,
    buff: float = 0.0,
    stroke_width: float = 5.0,
) -> Arrow:
    """An arrow from point in the direction of -grad_vec (descent direction).

    Theme defaults force a white stroke on Arrow, so we set stroke + fill
    explicitly here.
    """
    start = axes.c2p(float(point[0]), float(point[1]))
    end = axes.c2p(
        float(point[0] - scale * grad_vec[0]),
        float(point[1] - scale * grad_vec[1]),
    )
    arrow = Arrow(
        start=start, end=end, buff=buff,
        stroke_width=stroke_width, max_tip_length_to_length_ratio=0.35,
    )
    arrow.set_color(color)
    arrow.set_stroke(color=color, width=stroke_width)
    return arrow


def make_2d_axes(
    *,
    x_range: tuple[float, float, float] = (-3.5, 3.5, 1.0),
    y_range: tuple[float, float, float] = (-3.0, 3.0, 1.0),
    width: float = 6.5,
    height: float = 5.0,
) -> Axes:
    ax = Axes(
        x_range=x_range,
        y_range=y_range,
        x_length=width,
        y_length=height,
        tips=False,
        axis_config={"stroke_color": C_AXIS, "include_numbers": False},
    )
    return ax


def make_3d_axes(
    *,
    x_range: tuple[float, float, float] = (-3.0, 3.0, 1.0),
    y_range: tuple[float, float, float] = (-3.0, 3.0, 1.0),
    z_range: tuple[float, float, float] = (0.0, 20.0, 5.0),
    x_length: float = 5.5,
    y_length: float = 5.5,
    z_length: float = 3.2,
) -> ThreeDAxes:
    return ThreeDAxes(
        x_range=x_range,
        y_range=y_range,
        z_range=z_range,
        x_length=x_length,
        y_length=y_length,
        z_length=z_length,
        axis_config={"stroke_color": C_AXIS, "include_numbers": False, "stroke_width": 2.0},
        tips=False,
    )


def loss_surface(
    axes: ThreeDAxes,
    *,
    a_x: float = A_X,
    a_y: float = A_Y,
    resolution: tuple[int, int] = (40, 40),
) -> Surface:
    surf = Surface(
        lambda u, v: axes.c2p(u, v, 0.5 * a_x * u * u + 0.5 * a_y * v * v),
        u_range=(-3.0, 3.0),
        v_range=(-3.0, 3.0),
        resolution=resolution,
        should_make_jagged=False,
    )
    surf.set_style(fill_opacity=0.45, stroke_color=GREY_D, stroke_width=0.5)
    surf.set_fill_by_value(
        axes=axes,
        colorscale=[(BLUE, 0.0), (GREEN, 6.0), (YELLOW, 12.0), (RED, 18.0)],
        axis=2,
    )
    return surf


def iterates_to_3d_path(
    axes: ThreeDAxes,
    pts: np.ndarray,
    *,
    z_lift: float = 0.05,
) -> Callable[[float], np.ndarray]:
    """Return a parametric `t -> (x, y, z)` curve that walks the iterates.

    `z` is set from the loss surface plus a small lift so the curve sits
    just above the surface. The closure pre-computes all 3D points once.
    """
    coords = [
        axes.c2p(float(p[0]), float(p[1]), float(loss(p[0], p[1])) + z_lift)
        for p in pts
    ]

    def path(t: float) -> np.ndarray:
        t = max(0.0, min(1.0, t))
        idx = t * (len(coords) - 1)
        i = int(np.floor(idx))
        j = min(i + 1, len(coords) - 1)
        frac = idx - i
        return (1.0 - frac) * np.asarray(coords[i]) + frac * np.asarray(coords[j])

    return path


__all__ = [
    "A_X", "A_Y", "BETA_ADAM", "C_ADAM", "C_AXIS", "C_DIM", "C_GD",
    "C_MOMENTUM", "C_OPTIMUM", "C_TRAIL", "C_VARIANCE", "EPS_ADAGRAD",
    "EPS_ADAM", "GAMMA_ADAM", "GAMMA_MOMENTUM", "LR_ADAGRAD", "LR_ADAM",
    "LR_GD", "LR_MOMENTUM", "N_STEPS", "OptState", "START_POINT",
    "adagrad_step", "adam_step", "contour_quad", "gd_step",
    "glowing_dot", "grad", "gradient_arrow", "iterates_to_3d_path",
    "loss", "loss_surface", "make_2d_axes", "make_3d_axes",
    "momentum_step", "run_optimizer", "trail_from_points",
]
