"""Renderer compatibility helpers for ManimCE Cairo and OpenGL mobjects."""

from __future__ import annotations

from typing import Any, TypeGuard, cast

import numpy as np
from manim import Mobject, VMobject
from manim.mobject.opengl.opengl_mobject import OpenGLMobject
from manim.mobject.opengl.opengl_vectorized_mobject import OpenGLVMobject

type MobjectLike = Mobject | OpenGLMobject
type VMobjectLike = VMobject | OpenGLVMobject


def is_mobject(value: object) -> TypeGuard[MobjectLike]:
    """Return true for both Cairo and OpenGL Manim mobject instances."""
    return isinstance(value, (Mobject, OpenGLMobject))


def is_vmobject(value: object) -> TypeGuard[VMobjectLike]:
    """Return true for both Cairo and OpenGL vectorized mobject instances."""
    return isinstance(value, (VMobject, OpenGLVMobject))


def critical_point(mobject: MobjectLike, direction: np.ndarray) -> np.ndarray:
    """Return the bounding-box point matching ``direction`` on either renderer.

    Cairo mobjects expose ``get_critical_point``. OpenGL mobjects expose the
    same concept as ``get_bounding_box_point``.
    """
    if hasattr(mobject, "get_critical_point"):
        return np.asarray(cast(Any, mobject).get_critical_point(direction), dtype=float)
    if hasattr(mobject, "get_bounding_box_point"):
        return np.asarray(cast(Any, mobject).get_bounding_box_point(direction), dtype=float)
    raise TypeError(f"{type(mobject).__name__} has no critical-point API")


__all__ = ["MobjectLike", "VMobjectLike", "critical_point", "is_mobject", "is_vmobject"]
