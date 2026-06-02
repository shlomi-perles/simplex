"""Exit animation helpers: WeakKeyDictionary overrides, FadeOut fallback, kwargs forwarding."""

import gc
import weakref

from simplex.engine.animations import ExitAnim, clear_scene, exit_for, set_exit_animation


class _FakeMob:
    pass


class _FakeAnim:
    def __init__(self, mob: object, **kwargs: object) -> None:
        self.mob = mob
        self.kwargs = kwargs


def test_exitanim_falls_back_to_fadeout() -> None:
    from manim import FadeOut, Mobject

    anim = ExitAnim(Mobject())
    assert isinstance(anim, FadeOut)


def test_set_exit_animation_is_picked_up_by_exitanim() -> None:
    mob = _FakeMob()
    set_exit_animation(mob, _FakeAnim)
    anim = ExitAnim(mob, run_time=0.25)
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


def test_clear_scene_uses_all_scene_mobjects_even_with_canvas_pool() -> None:
    content = _FakeMob()
    canvas = _FakeMob()
    set_exit_animation(content, _FakeAnim)
    set_exit_animation(canvas, _FakeAnim)

    class _Scene:
        def __init__(self) -> None:
            self.mobjects = [content, canvas]
            self.mobjects_without_canvas = [content]
            self.played: tuple[_FakeAnim, ...] = ()

        def play(self, *animations: _FakeAnim) -> None:
            self.played = animations

    scene = _Scene()
    clear_scene(scene)

    assert [anim.mob for anim in scene.played] == [content, canvas]
