"""Updater-driven dynamics: `VT`, `DN`, orientation + stroke updaters.

Manim 0.20's `ValueTracker` already overloads arithmetic operators, so `VT`
adds only the operators that aren't there yet: `~vt` (read), `vt @ x` (animate
set), `vt @= x` (immediate set). `DN` is a `DecimalNumber` whose value is
auto-pulled from a `ValueTracker` or callable via an updater.
"""

from collections.abc import Callable
from typing import Any, Self

from manim import DecimalNumber, Line, Mobject, ValueTracker


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
    number.add_updater(lambda m: m.set_value(getter()))
    return number


def keep_orientation(scene: Any, *mobjects: Mobject) -> None:
    """Counter-rotate each mobject so it stays upright even when its parent rotates.

    Adds an invisible `Line` submobject to each target that records the
    parent's current angle; the scene-level updater rotates the rest of
    the mobject back by the inverse of that angle every frame.
    """
    for mob in mobjects:
        marker = Line().set_opacity(0).move_to(mob.get_center())
        mob.add(marker)

    def updater(_: float) -> None:
        for mob in mobjects:
            marker_line = mob[-1]
            mob[:-1].rotate(-marker_line.get_angle(), about_point=mob[:-1].get_center())

    scene.add_updater(updater)


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

        mobject.add_updater(update)
        return mobject

    for sub in mobject.get_family():
        maintain_apparent_stroke_width(sub, camera, recursive=sub is not mobject)
    return mobject


__all__ = ["DN", "VT", "keep_orientation", "maintain_apparent_stroke_width"]
