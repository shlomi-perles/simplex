"""Renderer-aware sphere mobjects."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import numpy as np
from manim import config
from manim.constants import ORIGIN, PI, TAU, RendererType
from manim.mobject.opengl.opengl_surface import OpenGLSurface
from manim.mobject.three_d import three_dimensions
from manim.typing import Point3D, Point3DLike

_OPENGL_SPHERE_RESOLUTION = (101, 51)


class OpenGLSphere(OpenGLSurface):
    """Manim-compatible sphere backed directly by ``OpenGLSurface``."""

    def __init__(
        self,
        center: Point3DLike = ORIGIN,
        radius: float = 1,
        resolution: int | Sequence[int] | None = None,
        u_range: tuple[float, float] = (0, TAU),
        v_range: tuple[float, float] = (0, PI),
        **kwargs: Any,
    ) -> None:
        self.radius = radius
        super().__init__(
            uv_func=self.func,
            resolution=_normalize_resolution(resolution),
            u_range=u_range,
            v_range=v_range,
            **kwargs,
        )
        self.shift(center)

    def func(self, u: float, v: float) -> Point3D:
        """Return the point on the sphere for Manim's standard ``(u, v)`` ranges."""
        return self.radius * np.array(
            [np.cos(u) * np.sin(v), np.sin(u) * np.sin(v), -np.cos(v)],
        )


def sphere_class() -> type[Any]:
    """Return Manim's sphere class, replacing it only when OpenGL needs help."""
    manim_sphere = three_dimensions.Sphere
    if _is_opengl_renderer() and not issubclass(manim_sphere, OpenGLSurface):
        return OpenGLSphere
    return manim_sphere


def install_opengl_sphere() -> None:
    """Patch Manim's public ``Sphere`` export for OpenGL render processes."""
    if not _is_opengl_renderer():
        return

    import manim

    if issubclass(three_dimensions.Sphere, OpenGLSurface):
        return

    three_dimensions.Sphere = OpenGLSphere
    manim.Sphere = OpenGLSphere


def _normalize_resolution(resolution: int | Sequence[int] | None) -> tuple[int, int]:
    if resolution is None:
        return _OPENGL_SPHERE_RESOLUTION
    if isinstance(resolution, int):
        return (resolution, resolution)
    u_resolution, v_resolution = resolution
    return (int(u_resolution), int(v_resolution))


def _is_opengl_renderer() -> bool:
    return config.renderer == RendererType.OPENGL


Sphere = sphere_class()

__all__ = ["OpenGLSphere", "Sphere", "install_opengl_sphere", "sphere_class"]
