"""Exit animation helpers: WeakKeyDictionary overrides, FadeOut fallback, kwargs forwarding."""

import gc
import weakref

from simplex.engine.animations import Remove, exit_for, set_exit_animation


class _FakeMob:
    pass


class _FakeAnim:
    def __init__(self, mob: object, **kwargs: object) -> None:
        self.mob = mob
        self.kwargs = kwargs


def test_remove_falls_back_to_fadeout() -> None:
    from manim import FadeOut, Mobject

    anim = Remove(Mobject())
    assert isinstance(anim, FadeOut)


def test_set_exit_animation_is_picked_up_by_remove() -> None:
    mob = _FakeMob()
    set_exit_animation(mob, _FakeAnim)
    anim = Remove(mob, run_time=0.25)
    assert isinstance(anim, _FakeAnim)
    assert anim.kwargs == {"run_time": 0.25}
    assert anim.mob is mob


def test_exit_for_forwards_kwargs() -> None:
    mob = _FakeMob()
    set_exit_animation(mob, _FakeAnim)
    anim = exit_for(mob, shift=(0, 1, 0))
    assert anim.kwargs == {"shift": (0, 1, 0)}


def test_set_exit_animation_does_not_pollute_mob_attributes() -> None:
    """Override storage is external (WeakKeyDictionary); no _simplex_exit on the mob."""
    mob = _FakeMob()
    set_exit_animation(mob, _FakeAnim)
    assert not hasattr(mob, "_simplex_exit")


def test_override_is_garbage_collected_with_mob() -> None:
    """The WeakKeyDictionary does not keep the mob alive."""
    mob = _FakeMob()
    ref = weakref.ref(mob)
    set_exit_animation(mob, _FakeAnim)
    del mob
    gc.collect()
    assert ref() is None
