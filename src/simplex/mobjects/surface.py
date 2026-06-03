"""Scalar-field-colored OpenGL surfaces and color-bar legend.

New mobjects:

* **ScalarFieldSurface** -- ``OpenGLSurface`` whose per-vertex color is
  derived from an arbitrary scalar function of ``(u, v)`` or ``(x, y, z)``.
* **ColorBar** -- vertical gradient legend showing the value-to-color mapping.
* **colorize_surface** -- standalone helper that applies scalar-field coloring
  to any existing ``OpenGLSurface``.

Named colormaps (passed as a string, e.g. ``colormap="viridis"``) are
resolved through the lightweight ``cmap`` package. Any name accepted by
``cmap.Colormap(name)`` works (all standard matplotlib names are
supported without pulling in matplotlib itself).
"""

from __future__ import annotations

import inspect
from collections.abc import Callable, Sequence
from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    from manim.opengl import OpenGLMobject

import numpy as np
from manim import (
    BLUE,
    GREEN,
    RED,
    RIGHT,
    UP,
    YELLOW,
    DecimalNumber,
    Rectangle,
    VGroup,
)
from manim.mobject.opengl.opengl_compatibility import ConvertToOpenGL
from manim.opengl import OpenGLSurface
from manim.typing import Point2DLike, Point3DLike
from manim.utils.color import ManimColor, ParsableManimColor, color_to_rgba, interpolate_color

type _ScalarInput = float | int | np.ndarray
type _ScalarResult = float | int | np.ndarray
type _ScalarFunc2D = Callable[[_ScalarInput, _ScalarInput], _ScalarResult]
type _ScalarFunc3D = Callable[[_ScalarInput, _ScalarInput, _ScalarInput], _ScalarResult]
type _ScalarFunc = _ScalarFunc2D | _ScalarFunc3D

__all__ = [
    "ColorBar",
    "ScalarFieldSurface",
    "colorize_surface",
]


_MPL_SAMPLES = 256


# ── Internal helpers ──────────────────────────────────────────────


def _resolve_colormap(
    colormap: str | Sequence[ParsableManimColor], n_samples: int = _MPL_SAMPLES
) -> list[ManimColor]:
    """Return a list of ``ManimColor`` objects from *colormap*.

    *colormap* is either a sequence of colors (hex strings, ManimColor,
    or Manim color constants) or a **cmap colormap name** such as
    ``"viridis"``, ``"coolwarm"``, or ``"plasma"``.
    """
    if isinstance(colormap, str):
        from cmap import Colormap

        cmap_obj = Colormap(colormap)
        return [ManimColor(cmap_obj(t).hex) for t in np.linspace(0, 1, n_samples)]
    return [ManimColor(c) for c in colormap]


def _detect_arity(func: _ScalarFunc) -> int:
    sig = inspect.signature(func)
    return sum(
        1
        for p in sig.parameters.values()
        if p.default is inspect.Parameter.empty
        and p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)
    )


def _float_pair(values: object, *, name: str) -> tuple[float, float]:
    arr = np.asarray(values, dtype=float)
    if arr.shape != (2,):
        raise ValueError(f"{name} must contain exactly two values, got shape {arr.shape}")
    return float(arr[0]), float(arr[1])


def _scalars_to_rgba(
    scalars: np.ndarray,
    colormap: list[ManimColor],
    opacity: float,
    color_range: tuple[float, float] | None,
) -> np.ndarray:
    vmin, vmax = (
        (float(scalars.min()), float(scalars.max())) if color_range is None else color_range
    )
    if vmax <= vmin:
        vmax = vmin + 1.0

    normalized = np.clip((scalars - vmin) / (vmax - vmin), 0, 1)
    n = len(colormap)
    t = normalized * (n - 1)
    idx = np.floor(t).astype(int)
    frac = t - idx
    idx_next = np.minimum(idx + 1, n - 1)

    rgba_stops = np.array([color_to_rgba(c, opacity) for c in colormap], dtype=np.float32)
    c0, c1 = rgba_stops[idx], rgba_stops[idx_next]
    return (c0 + (c1 - c0) * frac[..., np.newaxis]).astype(np.float32)


def _eval_scalar_field(
    func: _ScalarFunc,
    surface: OpenGLSurface,
    arity: int,
) -> np.ndarray:
    nu, nv = surface.resolution
    if arity == 2:
        u_vals = np.linspace(*_float_pair(surface.u_range, name="u_range"), nu)
        v_vals = np.linspace(*_float_pair(surface.v_range, name="v_range"), nv)
        uu, vv = np.meshgrid(u_vals, v_vals, indexing="ij")
        func2 = cast(_ScalarFunc2D, func)
        try:
            result = np.asarray(func2(uu, vv))
            if result.shape == (nu, nv):
                return result.ravel()
        except (TypeError, ValueError):
            pass
        return np.vectorize(func2)(uu, vv).ravel()

    s_points = surface.get_surface_points_and_nudged_points()[0]
    func3 = cast(_ScalarFunc3D, func)
    try:
        result = np.asarray(func3(s_points[:, 0], s_points[:, 1], s_points[:, 2]))
        if result.shape == (len(s_points),):
            return result
    except (TypeError, ValueError):
        pass
    return np.asarray([func3(p[0], p[1], p[2]) for p in s_points])


def _interpolate_cmap(cmap: list[ManimColor], t: float) -> ManimColor:
    t = max(0.0, min(1.0, t))
    n = len(cmap)
    scaled = t * (n - 1)
    idx = int(scaled)
    frac = scaled - idx
    idx_next = min(idx + 1, n - 1)
    return interpolate_color(cmap[idx], cmap[idx_next], frac)


# ── Standalone helper ─────────────────────────────────────────────


def colorize_surface(
    surface: OpenGLSurface,
    color_func: _ScalarFunc,
    colormap: str | Sequence[ParsableManimColor] = (BLUE, GREEN, YELLOW, RED),
    color_range: tuple[float, float] | None = None,
) -> OpenGLSurface:
    """Apply scalar-field coloring to any ``OpenGLSurface``.

    Parameters
    ----------
    surface
        Target surface (modified in place).
    color_func
        ``(u, v) -> scalar`` or ``(x, y, z) -> scalar``.
        Arity auto-detected; vectorized NumPy calls attempted first.
    colormap
        Color list or a key from ``COLORMAPS``.
    color_range
        Fixed ``(min, max)``; *None* auto-scales to data range.
    """
    cmap = _resolve_colormap(colormap)
    arity = _detect_arity(color_func)
    scalars = _eval_scalar_field(color_func, surface, arity)
    surface.color_by_val = _scalars_to_rgba(scalars, cmap, surface.get_opacity(), color_range)  # type: ignore[assignment]  # ndarray accepted at runtime
    surface.colorscale = True
    return surface


# ── ScalarFieldSurface ────────────────────────────────────────────


class ScalarFieldSurface(OpenGLSurface):
    """``OpenGLSurface`` with built-in scalar-field coloring.

    Pass *color_func* at construction time or later via ``set_color_func``.
    Inside an updater, call ``refresh_colors`` after rebuilding geometry::

        surface = ScalarFieldSurface(
            lambda u, v: np.array([u, v, np.sin(u) * np.cos(v)]),
            u_range=[-PI, PI], v_range=[-PI, PI],
            color_func="height",
            colormap="thermal",
        )

    String presets for *color_func*: ``"height"`` (z-value), ``"radial"``
    (distance from origin), ``"angle"`` (azimuthal angle in xy-plane).

    Static factories ``height_func``, ``distance_from``, ``angle_around``
    return callables for parameterised variants.
    """

    def __init__(
        self,
        uv_func: _ScalarFunc | None = None,
        *,
        color_func: _ScalarFunc | str | None = None,
        colormap: str | Sequence[ParsableManimColor] = (BLUE, GREEN, YELLOW, RED),
        color_range: tuple[float, float] | None = None,
        **kwargs: Any,
    ) -> None:
        self._color_func: _ScalarFunc | str | None = color_func
        self._colormap = _resolve_colormap(colormap)
        self._color_range = color_range
        self._arity_cache: int | None = None

        kwargs.pop("colorscale", None)
        super().__init__(uv_func=uv_func, **kwargs)

        if self._color_func is not None:
            self.refresh_colors()

    # ── Public API ────────────────────────────────────────────

    def set_color_func(
        self,
        color_func: _ScalarFunc | str,
        *,
        colormap: str | Sequence[ParsableManimColor] | None = None,
        color_range: tuple[float, float] | None = None,
    ) -> ScalarFieldSurface:
        """Replace the scalar-field function and recompute colors.

        *None* for *colormap* / *color_range* keeps the current value.
        Use ``auto_color_range`` to explicitly reset to auto-scaling.
        """
        self._color_func = color_func
        self._arity_cache = None
        if colormap is not None:
            self._colormap = _resolve_colormap(colormap)
        if color_range is not None:
            self._color_range = color_range
        self.refresh_colors()
        return self

    def set_colormap(self, colormap: str | Sequence[ParsableManimColor]) -> ScalarFieldSurface:
        """Change the colormap and recompute."""
        self._colormap = _resolve_colormap(colormap)
        self.refresh_colors()
        return self

    def set_color_range(self, vmin: float, vmax: float) -> ScalarFieldSurface:
        """Pin the scalar range (disables auto-scaling)."""
        self._color_range = (vmin, vmax)
        self.refresh_colors()
        return self

    def auto_color_range(self) -> ScalarFieldSurface:
        """Reset to auto-scaled color range."""
        self._color_range = None
        self.refresh_colors()
        return self

    def refresh_colors(self) -> ScalarFieldSurface:
        """Recompute per-vertex colors from the current scalar function.

        Call inside an updater whenever geometry or tracked values change::

            def updater(surf):
                # ... rebuild points ...
                surf.refresh_colors()

            surface.add_updater(updater)
        """
        func = self._resolved_func()
        if func is None:
            return self
        arity = self._get_arity(func)
        scalars = _eval_scalar_field(func, self, arity)
        self.color_by_val = _scalars_to_rgba(  # type: ignore[assignment]  # ndarray accepted at runtime
            scalars, self._colormap, self.get_opacity(), self._color_range
        )
        self.colorscale = True
        return self

    # ── Preset factories ──────────────────────────────────────

    @staticmethod
    def height_func() -> _ScalarFunc3D:
        """``(x, y, z) -> z``"""

        def height(_x: _ScalarInput, _y: _ScalarInput, z: _ScalarInput) -> _ScalarResult:
            return z

        return height

    @staticmethod
    def distance_from(center: Point3DLike = (0, 0, 0)) -> _ScalarFunc3D:
        """``(x, y, z) -> euclidean distance to center``"""
        center_arr = np.asarray(center, dtype=float)
        if center_arr.shape != (3,):
            raise ValueError(
                f"center must contain exactly three values, got shape {center_arr.shape}"
            )
        cx, cy, cz = (float(v) for v in center_arr)

        def distance(x: _ScalarInput, y: _ScalarInput, z: _ScalarInput) -> _ScalarResult:
            return np.sqrt((x - cx) ** 2 + (y - cy) ** 2 + (z - cz) ** 2)

        return distance

    @staticmethod
    def angle_around(center: Point2DLike = (0, 0)) -> _ScalarFunc3D:
        """``(x, y, z) -> atan2(y - cy, x - cx)``"""
        cx, cy = _float_pair(center, name="center")

        def angle(x: _ScalarInput, y: _ScalarInput, _z: _ScalarInput) -> _ScalarResult:
            return np.arctan2(y - cy, x - cx)

        return angle

    # ── Interpolation ────────────────────────────────────────

    def interpolate(
        self,
        mobject1: OpenGLMobject,
        mobject2: OpenGLMobject,
        alpha: float,
        *args: Any,
        **kwargs: Any,
    ) -> ScalarFieldSurface:
        super().interpolate(mobject1, mobject2, alpha, *args, **kwargs)
        c1 = self._extract_vertex_colors(mobject1)
        c2 = self._extract_vertex_colors(mobject2)
        if c1 is not None and c2 is not None and len(c1) == len(c2):
            self.color_by_val = c1 + (c2 - c1) * alpha
            self.colorscale = True
        return self

    @staticmethod
    def _extract_vertex_colors(mobject: OpenGLMobject) -> np.ndarray | None:
        cbv = getattr(mobject, "color_by_val", None)
        if isinstance(cbv, np.ndarray) and len(cbv) > 0:
            return np.asarray(cbv, dtype=np.float32)
        n = len(mobject.points) // 3
        if n == 0:
            return None
        rgbas = mobject.rgbas
        if len(rgbas) == 0:
            return None
        if len(rgbas) >= n:
            return np.asarray(rgbas[:n], dtype=np.float32)
        return np.broadcast_to(rgbas[:1], (n, 4)).copy().astype(np.float32)

    # ── Internals ─────────────────────────────────────────────

    def _resolved_func(self) -> _ScalarFunc | None:
        func = self._color_func
        if func is None:
            return None
        if isinstance(func, str):
            presets: dict[str, Callable[[], _ScalarFunc]] = {
                "height": self.height_func,
                "radial": lambda: self.distance_from(),
                "angle": lambda: self.angle_around(),
            }
            factory = presets.get(func)
            if factory is None:
                raise ValueError(f"Unknown preset {func!r}. Choose from {sorted(presets)}")
            return factory()
        return func

    def _get_arity(self, func: _ScalarFunc) -> int:
        if self._arity_cache is not None:
            return self._arity_cache
        self._arity_cache = _detect_arity(func)
        return self._arity_cache


# ── ColorBar ──────────────────────────────────────────────────────


class ColorBar(VGroup, metaclass=ConvertToOpenGL):
    """Vertical gradient legend for a scalar colormap.

    In a ``ThreeDSlide`` / ``ThreeDScene``, pin to the screen with
    ``self.add_fixed_in_frame_mobjects(bar)``::

        bar = ColorBar(colormap="thermal", min_value=-1, max_value=1)
        bar.to_edge(RIGHT)
        self.add_fixed_in_frame_mobjects(bar)
    """

    def __init__(
        self,
        colormap: str | Sequence[ParsableManimColor] = (BLUE, GREEN, YELLOW, RED),
        min_value: float = 0.0,
        max_value: float = 1.0,
        *,
        height: float = 3.0,
        width: float = 0.3,
        n_labels: int = 5,
        num_decimal_places: int = 1,
        font_size: float = 24,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        cmap = _resolve_colormap(colormap)

        n_bars = 50
        bar_h = height / n_bars
        bars = VGroup()
        for i in range(n_bars):
            t = i / max(n_bars - 1, 1)
            color = _interpolate_cmap(cmap, t)
            rect = Rectangle(
                width=width,
                height=bar_h * 1.05,
                fill_color=color,
                fill_opacity=1.0,
                stroke_width=0,
            )
            rect.move_to(UP * (i * bar_h - height / 2 + bar_h / 2))
            bars.add(rect)
        self.add(bars)

        labels = VGroup()
        for i in range(n_labels):
            t = i / max(n_labels - 1, 1)
            value = min_value + t * (max_value - min_value)
            label = DecimalNumber(
                value,
                num_decimal_places=num_decimal_places,
                font_size=font_size,
            )
            y_pos = t * height - height / 2
            label.next_to(bars, RIGHT, buff=0.15).set_y(y_pos)
            labels.add(label)
        self.add(labels)

        self.bars = bars
        self.labels = labels
