"""Default-exit registry, ``Remove``, ``set_exit_animation``, and ``clear_scene``.

Each Mobject type has a default *exit* animation (e.g. ``Tex`` -> ``Unwrite``,
``Circle`` -> ``ShrinkToCenter``). Callers can override per-instance via
``set_exit_animation(mob, anim_cls_or_factory)``, or per-type via
``register_exit(type, factory)``.

``Remove(mob)`` and ``clear_scene(scene, exclude=...)`` both dispatch through
``exit_for(mob)``, which checks instance overrides, then walks the MRO of
``type(mob)`` against the type defaults, falling back to ``FadeOut``.

Implementation notes:

- The type defaults dict is wrapped in a ``_DefaultRegistry`` singleton with
  a double-checked ``threading.Lock`` around its lazy init. Manim renders are
  mostly single-threaded but plugins can be poked from setup hooks running
  in parallel (e.g. test suites), so the lock is cheap insurance.
- Per-instance overrides are kept in a ``WeakKeyDictionary`` keyed by the
  Mobject, *not* monkey-patched onto the Mobject as a ``_simplex_exit``
  attribute. Manim's Mobject base is plain-class so both ``__hash__`` (id
  identity) and ``__weakref__`` work; if a downstream subclass disables one
  of these the override call fails fast at ``set_exit_animation`` time
  rather than leaking through a swallowed ``setattr``.
"""

import threading
from collections.abc import Callable, Iterable
from typing import Any
from weakref import WeakKeyDictionary

ExitFactory = Callable[..., Any]


class _DefaultRegistry:
    """Type -> exit-factory map with double-checked locked lazy init."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._map: dict[type, ExitFactory] | None = None

    def get(self) -> dict[type, ExitFactory]:
        if self._map is None:
            with self._lock:
                if self._map is None:
                    self._map = self._build()
        return self._map

    @staticmethod
    def _build() -> dict[type, ExitFactory]:
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

        from simplex.mobjects.paper import DismissPaper, Paper

        def fade_with_drift(m: Any, **kw: Any) -> Any:
            return FadeOut(m, shift=0.1 * DOWN, **kw)

        def paper_exit(m: Any, **kw: Any) -> Any:
            return DismissPaper(m, **kw)

        return {
            Paper: paper_exit,
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
            VMobject: fade_with_drift,
        }


_REGISTRY = _DefaultRegistry()
_OVERRIDES: WeakKeyDictionary[Any, ExitFactory] = WeakKeyDictionary()


def register_exit(mob_type: type, factory: ExitFactory) -> None:
    """Register a default exit animation for ``mob_type`` (and subclasses via MRO).

    ``factory(mob, **kwargs)`` must return an ``Animation``. Most callers pass
    an ``Animation`` class directly (``Unwrite``, ``FadeOut``, ...) since
    classes are callable in this signature.
    """
    _REGISTRY.get()[mob_type] = factory


def set_exit_animation(mob: Any, factory: ExitFactory) -> Any:
    """Stash a per-instance exit factory for ``mob``. Returns ``mob`` for chaining.

    The override lives in a module-level ``WeakKeyDictionary`` -- it disappears
    automatically when ``mob`` is garbage-collected. No attribute is set on
    the Mobject itself.
    """
    try:
        _OVERRIDES[mob] = factory
    except TypeError as exc:  # mob is not hashable or weakref-able
        raise TypeError(
            f"set_exit_animation: {type(mob).__name__} cannot be used as a "
            "registry key (no __weakref__ or unhashable). Wrap the mobject "
            "in a VGroup or pass a different mobject."
        ) from exc
    return mob


def exit_for(mob: Any, **kwargs: Any) -> Any:
    """Return an ``Animation`` that exits ``mob``.

    Resolution order:

    1. per-instance override registered by ``set_exit_animation``;
    2. exact type or MRO match in the default registry;
    3. ``FadeOut`` fallback.

    Any ``**kwargs`` are forwarded to the resolved factory.
    """
    override = _OVERRIDES.get(mob)
    if override is not None:
        return override(mob, **kwargs) if kwargs else override(mob)
    defaults = _REGISTRY.get()
    for cls in type(mob).__mro__:
        factory = defaults.get(cls)
        if factory is not None:
            return factory(mob, **kwargs) if kwargs else factory(mob)
    from manim import FadeOut

    return FadeOut(mob, **kwargs)


def Remove(mob: Any, **kwargs: Any) -> Any:  # noqa: N802 -- mirrors Manim's PascalCase Animations
    """Alias for ``exit_for(mob, **kwargs)`` -- spelled to match Manim animations."""
    return exit_for(mob, **kwargs)


def clear_scene(scene: Any, *, exclude: Iterable[Any] = ()) -> None:
    """Play exit animations for every Mobject not in ``exclude``.

    Uses ``scene.mobjects_without_canvas`` when available (so the
    manim-slides canvas survives) and dispatches through ``exit_for`` so
    per-instance and per-type overrides apply.
    """
    skip = set(exclude)
    pool = getattr(scene, "mobjects_without_canvas", None) or scene.mobjects
    targets = [m for m in pool if m not in skip]
    if not targets:
        return
    scene.play(*(exit_for(m) for m in targets))
