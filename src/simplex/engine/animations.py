"""Default-exit registry, `Remove`, `set_exit_animation`, and `clear_scene`.

Each Mobject type has a default "exit" animation (e.g. `Tex` → `Unwrite`,
`Circle` → `ShrinkToCenter`). Callers can override per-instance via
`set_exit_animation(mob, anim_cls_or_factory)`, or per-type via
`register_exit(type, factory)`.

`Remove(mob)` and `clear_scene(scene, exclude=...)` both dispatch through
`exit_for(mob)`, which checks instance overrides, then walks the MRO of
`type(mob)` against `DEFAULT_EXITS`, falling back to `FadeOut`.
"""

from collections.abc import Callable, Iterable
from typing import Any

# Resolved lazily to avoid importing manim when this module is loaded by the
# reconcile / web / CLI paths.
_DEFAULTS_CACHE: dict[type, Callable[[Any], Any]] | None = None


def _build_defaults() -> dict[type, Callable[[Any], Any]]:
    from manim import (
        DOWN,
        Arrow,
        Circle,
        Code,
        DashedLine,
        Dot,
        FadeOut,
        Line,
        MarkupText,
        MathTex,
        ShrinkToCenter,
        Tex,
        Text,
        Uncreate,
        Unwrite,
        VMobject,
    )

    return {
        Tex: Unwrite,
        MathTex: Unwrite,
        Text: Unwrite,
        MarkupText: Unwrite,
        Code: Unwrite,
        Circle: ShrinkToCenter,
        Dot: ShrinkToCenter,
        Line: Uncreate,
        Arrow: Uncreate,
        DashedLine: Uncreate,
        VMobject: lambda m: FadeOut(m, shift=0.1 * DOWN),
    }


def _defaults() -> dict[type, Callable[[Any], Any]]:
    global _DEFAULTS_CACHE
    if _DEFAULTS_CACHE is None:
        _DEFAULTS_CACHE = _build_defaults()
    return _DEFAULTS_CACHE


def register_exit(mob_type: type, factory: Callable[[Any], Any]) -> None:
    """Register a default exit animation for `mob_type` (and subclasses via MRO).

    `factory(mob)` must return an `Animation`. Most callers pass an
    `Animation` class directly (`Unwrite`, `FadeOut`, ...) since classes are
    callable in this signature.
    """
    _defaults()[mob_type] = factory


def exit_for(mob: Any) -> Any:
    """Return an `Animation` that exits `mob`.

    Resolution order:
    1. `mob._simplex_exit` (per-instance override set by `set_exit_animation`)
    2. exact-type or MRO match in `DEFAULT_EXITS`
    3. `FadeOut` fallback
    """
    override = getattr(mob, "_simplex_exit", None)
    if override is not None:
        return override(mob)
    defaults = _defaults()
    for cls in type(mob).__mro__:
        factory = defaults.get(cls)
        if factory is not None:
            return factory(mob)
    from manim import FadeOut

    return FadeOut(mob)


def Remove(mob: Any, **kwargs: Any) -> Any:  # noqa: N802 -- mirrors Manim casing
    """Return the exit animation registered for `mob`.

    Backwards-compatible signature: `**kwargs` are forwarded only when the
    resolved factory is a plain class call (no per-instance override).
    """
    override = getattr(mob, "_simplex_exit", None)
    if override is not None:
        return override(mob, **kwargs) if kwargs else override(mob)
    defaults = _defaults()
    for cls in type(mob).__mro__:
        factory = defaults.get(cls)
        if factory is not None:
            return factory(mob) if not kwargs else factory(mob, **kwargs)
    from manim import FadeOut

    return FadeOut(mob, **kwargs)


def set_exit_animation(mob: Any, factory: Callable[[Any], Any] | type) -> Any:
    """Stash a custom exit animation factory on the Mobject. Returns `mob`."""
    mob._simplex_exit = factory
    return mob


def clear_scene(scene: Any, *, exclude: Iterable[Any] = ()) -> None:
    """Play exit animations for every mobject not in `exclude`.

    Uses `scene.mobjects_without_canvas` (manim-slides canvas survives) and
    dispatches through `exit_for` so per-instance / per-type overrides apply.
    """
    skip = set(exclude)
    pool = getattr(scene, "mobjects_without_canvas", None) or scene.mobjects
    targets = [m for m in pool if m not in skip]
    if not targets:
        return
    scene.play(*(exit_for(m) for m in targets))
