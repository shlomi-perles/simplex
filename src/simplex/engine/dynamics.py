"""Updater-driven dynamics: `VT`, `DN`, orientation + stroke updaters.

Manim 0.20's `ValueTracker` already overloads arithmetic operators, so `VT`
adds only the operators that aren't there yet: `~vt` (read), `vt @ x` (animate
set), `vt @= x` (immediate set). `DN` is a `DecimalNumber` whose value is
auto-pulled from a `ValueTracker` or callable via an updater.
"""

from collections.abc import Callable
from typing import Any, Self
from weakref import WeakKeyDictionary

from manim import DecimalNumber, Group, Line, Mobject, ValueTracker


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


_ORIENTATION_MARKERS: WeakKeyDictionary[Mobject, Line] = WeakKeyDictionary()


def keep_orientation(*mobjects: Mobject) -> None:
    """Counter-rotate each mobject so it stays upright as it rotates with a parent.

    Attaches a per-mobject updater (Manim 0.20.x ``mob.add_updater``) instead
    of polluting the scene's global updater list. The orientation tracker is
    a hidden :class:`~.Line` added as a submobject (so it rotates along with
    the parent), but the marker is looked up through a module-level
    ``WeakKeyDictionary`` -- callers never see it via ``mob[-1]``. Iterate
    ``mob.submobjects`` directly and skip whatever ``WeakKeyDictionary``
    returns if you need the user-visible children.
    """
    for mob in mobjects:
        marker = Line().set_opacity(0).move_to(mob.get_center())
        _ORIENTATION_MARKERS[mob] = marker
        mob.add(marker)

        def _counter_rotate(m: Mobject) -> None:
            tracker = _ORIENTATION_MARKERS.get(m)
            if tracker is None:
                return
            visible_children = [child for child in m.submobjects if child is not tracker]
            if not visible_children:
                return
            # Wrap in a transient ``Group`` so the rotation pivot matches the
            # bounding-box center of the user-visible children -- the same
            # semantics as ``mob[:-1].get_center()`` in the original
            # marker-as-last-submobject implementation, minus the ``mob[-1]``
            # ambiguity for downstream callers.
            visible = Group(*visible_children)
            visible.rotate(-tracker.get_angle(), about_point=visible.get_center())

        mob.add_updater(_counter_rotate)


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
