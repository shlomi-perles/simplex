"""Updater-driven dynamics: `VT`, `DN`, orientation + stroke updaters.

Manim 0.20's `ValueTracker` already overloads arithmetic operators, so `VT`
adds only the operators that aren't there yet: `~vt` (read), `vt @ x` (animate
set), `vt @= x` (immediate set). `DN` is a `DecimalNumber` whose value is
auto-pulled from a `ValueTracker` or callable via an updater.
"""

from collections.abc import Callable
from typing import Any, Self

import numpy as np
from manim import DecimalNumber, Mobject, ValueTracker, angle_of_vector


class VT(ValueTracker):
    """`ValueTracker` plus `~`, `@`, `@=` sugar (originally @Abulafia on Manim Discord).

    - `~vt` -> `vt.get_value()`
    - `vt @ x` -> `vt.animate.set_value(x)` (use inside `self.play`)
    - `vt @= x` -> `vt.set_value(x)` in place
    """

    def __invert__(self) -> float:
        return self.get_value()

    def __matmul__(self, value: float) -> Any:
        return self.animate.set_value(value)

    def __imatmul__(self, value: float) -> Self:
        self.set_value(value)
        return self


def DN(  # noqa: N802 -- mirrors the original `DN` shorthand
    source: ValueTracker | Callable[[], float],
    *args: Any,
    **kwargs: Any,
) -> DecimalNumber:
    """`DecimalNumber` that auto-tracks a `ValueTracker` or zero-arg callable.

    The returned mobject already has an updater attached, so just `add` it
    to the scene -- the displayed value follows `source` every frame.
    """
    if isinstance(source, ValueTracker):
        getter: Callable[[], float] = source.get_value
    elif callable(source):
        getter = source
    else:
        raise TypeError("DN source must be a ValueTracker or a zero-arg callable.")
    number = DecimalNumber(getter(), *args, **kwargs)
    number.add_updater(
        lambda m: m.set_value(getter())
    )  # TODO: change to use `always` (manim v0.20.1)
    return number


def keep_orientation(*mobjects: Mobject) -> None:
    """Counter-rotate each mobject so it stays upright as its parent rotates.

    Per-mobject updater (Manim 0.20.x ``add_updater``). The cumulative
    parent rotation is read from the mob's own
    :meth:`~.Mobject.get_points_defining_boundary` -- no hidden marker
    submobject is added, so iterating ``mob.submobjects`` returns only
    the user-visible children and setting opacity won't reveal anything
    unexpected.

    Setup snapshots the centroid-to-farthest-boundary-point vector;
    each frame the same vector is re-derived and the mob is rotated so
    its angle matches the snapshot. Counter-rotation snaps the points
    back to the snapshot, so the next parent rotation is again
    observable -- a self-correcting loop. Mobs with fewer than two
    boundary points (e.g., bare ``Mobject``, single ``Dot``) are
    silently skipped since "upright" has no meaning for them.
    """
    for mob in mobjects:
        boundary = mob.get_points_defining_boundary()
        if len(boundary) < 2:
            continue
        offsets = boundary - boundary.mean(axis=0)
        # Farthest point from the centroid is the most numerically stable
        # reference -- short offsets amplify angle noise.
        ref_index = int(np.linalg.norm(offsets, axis=1).argmax())
        if np.linalg.norm(offsets[ref_index]) < 1e-9:
            continue
        initial_angle = angle_of_vector(offsets[ref_index])

        def _upright(m: Mobject, _idx: int = ref_index, _initial: float = initial_angle) -> None:
            points = mob.get_points_defining_boundary()
            if len(points) <= _idx:
                return
            delta = angle_of_vector(points[_idx] - points.mean(axis=0)) - _initial
            if abs(delta) > 1e-9:
                center = m.get_center()
                m.rotate(-delta, about_point=points.mean(axis=0))
                m.move_to(center)

        mob.add_updater(_upright)


def maintain_apparent_stroke_width(
    mobject: Mobject,
    camera: Any,
    *,
    recursive: bool = True,
) -> Mobject:
    """Counter-scale stroke widths so they look constant under camera zoom.

    Walks the mobject family by default; pass `recursive=False` to only
    pin the top-level mobject's stroke width.
    """
    if not recursive or not mobject.submobjects:
        original_width = mobject.get_stroke_width()
        original_camera_width = camera.frame.get_width()

        def update(mob: Mobject) -> None:
            mob.set_stroke(width=original_width * original_camera_width / camera.frame.get_width())

        mobject.add_updater(update)  # TODO: change to use `always` (manim v0.20.1)
        return mobject

    for sub in mobject.get_family():
        maintain_apparent_stroke_width(sub, camera, recursive=sub is not mobject)
    return mobject


__all__ = ["DN", "VT", "keep_orientation", "maintain_apparent_stroke_width"]
