"""Renderer compatibility helpers for ManimCE Cairo and OpenGL mobjects."""

from __future__ import annotations

from typing import Any, TypeGuard, cast

import numpy as np
from manim import Mobject, VMobject
from manim.mobject.opengl.opengl_mobject import OpenGLMobject
from manim.mobject.opengl.opengl_vectorized_mobject import OpenGLVMobject

type MobjectLike = Mobject | OpenGLMobject
type VMobjectLike = VMobject | OpenGLVMobject
type ZIndex = int | float


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


def set_mobject_z_index(
    mobject: MobjectLike,
    z_index: ZIndex,
    *,
    family: bool = False,
) -> MobjectLike:
    """Set z-index on Cairo or OpenGL mobjects.

    Cairo mobjects expose ``set_z_index``. Some OpenGL mobjects only expose the
    ``z_index`` attribute, so this helper mirrors Manim's ``family=True`` shape
    by walking the mobject family when the method is unavailable.
    """
    set_z_index = getattr(mobject, "set_z_index", None)
    if callable(set_z_index):
        cast(Any, set_z_index)(z_index, family=family)
        return mobject

    targets = _mobject_family(mobject) if family else (mobject,)
    for target in targets:
        cast(Any, target).z_index = z_index
    return mobject


def _mobject_family(mobject: MobjectLike) -> tuple[MobjectLike, ...]:
    get_family = getattr(mobject, "get_family", None)
    if callable(get_family):
        return tuple(cast(Any, get_family)())

    children = tuple(child for child in getattr(mobject, "submobjects", ()) if is_mobject(child))
    return (mobject, *(descendant for child in children for descendant in _mobject_family(child)))


__all__ = [
    "MobjectLike",
    "VMobjectLike",
    "critical_point",
    "is_mobject",
    "is_vmobject",
    "set_mobject_z_index",
]
