"""Exit-animation helpers."""

from typing import Any


def Remove(mob: Any, **kwargs: Any) -> Any:  # noqa: N802 -- mirrors Manim casing
    """Return the exit animation registered on `mob`, falling back to `FadeOut`."""
    from manim import FadeOut

    anim_cls = getattr(mob, "_simplex_exit", None) or FadeOut
    return anim_cls(mob, **kwargs)


def set_exit_animation(mob: Any, anim_cls: type) -> Any:
    """Stash a custom exit animation class on the Mobject."""
    mob._simplex_exit = anim_cls
    return mob
