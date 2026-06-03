"""Renderer-aware sphere mobjects."""

from __future__ import annotations

import pytest

pytest.importorskip("manim")

from manim import config
from manim.constants import RendererType
from manim.mobject.opengl.opengl_surface import OpenGLSurface
from manim.mobject.three_d import three_dimensions

from simplex.mobjects.sphere import OpenGLSphere, install_opengl_sphere


def test_opengl_sphere_uses_opengl_surface_geometry() -> None:
    sphere = OpenGLSphere()

    assert isinstance(sphere, OpenGLSurface)
    assert sphere.resolution == (101, 51)
    assert len(sphere.points) == 3 * 101 * 51
    assert sphere.get_triangle_indices() is not None


def test_opengl_sphere_accepts_manim_sphere_resolution_int() -> None:
    sphere = OpenGLSphere(resolution=12)

    assert sphere.resolution == (12, 12)


def test_install_opengl_sphere_patches_manim_exports(monkeypatch: pytest.MonkeyPatch) -> None:
    import manim

    monkeypatch.setattr(config, "renderer", RendererType.OPENGL)
    monkeypatch.setattr(manim, "Sphere", three_dimensions.Sphere)
    monkeypatch.setattr(three_dimensions, "Sphere", three_dimensions.Sphere)

    install_opengl_sphere()

    assert manim.Sphere is OpenGLSphere
    assert three_dimensions.Sphere is OpenGLSphere


def test_install_opengl_sphere_leaves_cairo_exports(monkeypatch: pytest.MonkeyPatch) -> None:
    import manim

    class StubSphere:
        pass

    original = StubSphere
    monkeypatch.setattr(config, "renderer", RendererType.CAIRO)
    monkeypatch.setattr(manim, "Sphere", original)
    monkeypatch.setattr(three_dimensions, "Sphere", original)

    install_opengl_sphere()

    assert manim.Sphere is original
    assert three_dimensions.Sphere is original
