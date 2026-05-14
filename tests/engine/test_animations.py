"""Exit animation helpers."""

from simplex.engine.animations import Remove, set_exit_animation


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
