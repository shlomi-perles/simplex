# File length justification (STYLE.md: >300 lines requires a note):
# `TransformByGlyphMap` is one cohesive Animation class with several private
# branches (introducer / remover / double / show_indices / auto_*). Splitting
# the branches across modules would force callers to thread the same partial
# state through public seams; keeping them as private methods of one class is
# the simplest representation. `GhostSlideFade` is small but lives here so the
# whole "custom Animation classes derived from MF_Tools" lives in one file.
"""Glyph-aware Tex transforms and composite fade animations.

`TransformByGlyphMap` is the flagship: a richer alternative to Manim's
`TransformMatchingTex` / `TransformMatchingShapes` that lets you map glyph
indices explicitly, with per-entry kwargs (path_arc, run_time, delay) and an
auto `show_indices` mode for discovering the right index assignments.

`GhostSlideFade` is a single-mobject in-place animation that fades in, lives
for a configurable lifetime while shifting / scaling / rotating, then fades
out -- useful for ghosted transition cues over an unchanged scene.

Adapted from MF_Tools (John Connell) for Manim CE 0.20+. The `interpret_delay`
rate-func patch is preserved as-is because it is still the cleanest way to
shift sub-animations within an AnimationGroup; Manim 0.19's
`turn_animation_into_updater(anim, delay=0.5)` only handles updaters, not
sub-animations of an AnimationGroup.
"""

from typing import Any

import numpy as np
from manim import (
    BLACK,
    BLUE_D,
    DOWN,
    ORIGIN,
    RED_D,
    Animation,
    AnimationGroup,
    Create,
    FadeIn,
    FadeOut,
    Mobject,
    ReplacementTransform,
    VGroup,
    VMobject,
    Wait,
    index_labels,
    smooth,
)


def _is_animation_class(value: Any) -> bool:
    return isinstance(value, type) and issubclass(value, Animation)


def _is_empty_slot(value: Any) -> bool:
    """A glyph_map slot is 'empty' when it's an empty list or an Animation class."""
    return not value or _is_animation_class(value)


def _interpret_delay(opts: dict[str, Any]) -> dict[str, Any]:
    """Convert a `delay` kwarg into a stretched run_time + offset rate_func.

    Manim has no first-class delay on Animation, and Succession injects a
    boundary between sub-animations that disrupts AnimationGroup. Stretching
    the rate_func avoids both problems -- the animation simply waits at its
    starting state for `delay` seconds before its real curve begins.
    """
    delay = opts.pop("delay", 0)
    if delay == 0:
        return opts
    run_time = opts.pop("run_time", 1)
    new_run_time = delay + run_time
    rate_func = opts.pop("rate_func", smooth)
    fraction = delay / new_run_time

    def shifted(t: float) -> float:
        if t < fraction:
            return 0.0
        return rate_func((t - fraction) / (1 - fraction))

    opts["rate_func"] = shifted
    opts["run_time"] = new_run_time
    return opts


class TransformByGlyphMap(AnimationGroup):
    """Animate `mobA` -> `mobB` by mapping glyph indices explicitly.

    Each `glyph_map` entry is `(from_indices, to_indices, [kwargs])`:
      - both populated -> ReplacementTransform of those glyphs
      - empty `from_indices` -> introducer (default FadeIn) of `to_indices`
      - empty `to_indices`   -> remover (default FadeOut) of `from_indices`

    Special slot values: an empty list, or an `Animation` *class* used in
    place of the empty list to override the default introducer / remover.

    Per-entry kwargs accept everything the underlying animation accepts plus:
      - `delay`: seconds to wait before this sub-animation starts.
      - `transform_class`: alternate transformer (e.g. `FadeTransform`).

    Indices not mentioned in the map are auto-resolved:
      - default: `ReplacementTransform` pairs in order (requires equal counts).
      - `auto_fade=True`: FadeOut leftover from-glyphs, FadeIn leftover to-glyphs.
      - `auto_morph=True`: morph the leftover groups as one big VGroup pair.

    If the unmentioned counts mismatch (and neither auto mode is set),
    falls back to `show_indices` mode: stacks both mobjects and overlays
    coloured index labels so you can read off the right indices.

    See the showcase deck for runnable examples.
    """

    def __init__(
        self,
        mobA: VMobject,  # noqa: N803 -- mirrors source paper
        mobB: VMobject,  # noqa: N803
        *glyph_map: tuple[Any, ...],
        from_copy: bool = False,
        mobA_submobject_index: list[int] | None = None,  # noqa: N803
        mobB_submobject_index: list[int] | None = None,  # noqa: N803
        default_transformer: type[Animation] = ReplacementTransform,
        default_introducer: type[Animation] = FadeIn,
        default_remover: type[Animation] = FadeOut,
        introduce_individually: bool = False,
        remove_individually: bool = False,
        shift_fades: bool = False,
        auto_fade: bool = False,
        auto_morph: bool = False,
        auto_resolve_kwargs: dict[str, Any] | None = None,
        show_indices: bool = False,
        A_index_labels_color: str = RED_D,  # noqa: N803
        B_index_labels_color: str = BLUE_D,  # noqa: N803
        index_label_height: float = 0.2,
        printing: bool = False,
        **kwargs: Any,
    ) -> None:
        self.mobA = mobA
        self.mobB = mobB
        self.glyph_map = glyph_map
        self.default_transformer = default_transformer
        self.default_introducer = default_introducer
        self.default_remover = default_remover
        self.introduce_individually = introduce_individually
        self.remove_individually = remove_individually
        self.shift_fades = shift_fades
        self.auto_resolve_kwargs = auto_resolve_kwargs or {}
        self.printing = printing
        self.show_indices = show_indices or len(glyph_map) == 0

        a_path = mobA_submobject_index if mobA_submobject_index is not None else [0]
        b_path = mobB_submobject_index if mobB_submobject_index is not None else [0]

        a: VMobject = mobA.copy() if from_copy else mobA
        for i in a_path:
            a = a[i]
        b: VMobject = mobB
        for i in b_path:
            b = b[i]

        self.animations: list[Animation] = []
        self.mentioned_from: list[int] = []
        self.mentioned_to: list[int] = []

        for entry in glyph_map:
            self._process_entry(a, b, entry)

        self.remaining_from = [i for i in range(len(a)) if i not in self.mentioned_from]
        self.remaining_to = [i for i in range(len(b)) if i not in self.mentioned_to]

        if not auto_fade and not auto_morph:
            self._check_indices()

        if self.show_indices:
            self._build_show_indices(
                a, b, index_label_height, A_index_labels_color, B_index_labels_color
            )
            return

        if auto_fade:
            self._auto_fade(a, b)
        elif auto_morph:
            self._auto_morph(a, b)
        else:
            self._auto_transform(a, b)

        super().__init__(*self.animations, **kwargs)

    def _process_entry(self, a: VMobject, b: VMobject, entry: tuple[Any, ...]) -> None:
        if len(entry) not in (2, 3):
            raise ValueError(f"Invalid glyph_map entry (need 2 or 3 elements): {entry!r}")
        if self.printing:
            print(f"Glyph map entry: {entry!r}")  # noqa: T201

        slots = list(entry)
        if len(slots) == 2:
            slots.append({})
        opts: dict[str, Any] = slots[2]

        from_slot, to_slot = slots[0], slots[1]
        from_empty = _is_empty_slot(from_slot)
        to_empty = _is_empty_slot(to_slot)

        if from_empty and to_empty:
            # Pre-1.4 source treated `([], [])` as a show_indices trigger; the
            # current author disabled that to play nicely with MF_Algebra. We
            # follow the modern behaviour: silently skip the no-op entry.
            return
        if from_empty:
            self._add_introducer(a, b, from_slot, to_slot, opts)
        elif to_empty:
            self._add_remover(a, b, from_slot, to_slot, opts)
        else:
            self._add_double(a, b, from_slot, to_slot, opts)

    def _add_introducer(
        self,
        a: VMobject,
        b: VMobject,
        from_slot: Any,
        to_slot: list[int],
        opts: dict[str, Any],
    ) -> None:
        introducer: type[Animation] = from_slot if from_slot else self.default_introducer
        opts = _interpret_delay(opts)
        if introducer is FadeIn and self.shift_fades and "shift" not in opts:
            opts["shift"] = b.get_center() - a.get_center()
        targets = (
            [b[i] for i in to_slot]
            if self.introduce_individually
            else [VGroup(*(b[i] for i in to_slot))]
        )
        for mob in targets:
            self.animations.append(introducer(mob, **opts))
        self.mentioned_to.extend(to_slot)

    def _add_remover(
        self,
        a: VMobject,
        b: VMobject,
        from_slot: list[int],
        to_slot: Any,
        opts: dict[str, Any],
    ) -> None:
        remover: type[Animation] = to_slot if to_slot else self.default_remover
        opts = _interpret_delay(opts)
        if remover is FadeOut and self.shift_fades and "shift" not in opts:
            opts["shift"] = b.get_center() - a.get_center()
        targets = (
            [a[i] for i in from_slot]
            if self.remove_individually
            else [VGroup(*(a[i] for i in from_slot))]
        )
        for mob in targets:
            self.animations.append(remover(mob, **opts))
        self.mentioned_from.extend(from_slot)

    def _add_double(
        self,
        a: VMobject,
        b: VMobject,
        from_slot: list[int],
        to_slot: list[int],
        opts: dict[str, Any],
    ) -> None:
        transformer: type[Animation] = opts.pop("transform_class", self.default_transformer)
        opts = _interpret_delay(opts)
        # Indices already used by an earlier entry need a copy so the prior
        # animation isn't disturbed when this one grabs the same glyph.
        from_mob = VGroup(*(a[i].copy() if i in self.mentioned_from else a[i] for i in from_slot))
        to_mob = VGroup(*(b[i] for i in to_slot))
        self.animations.append(transformer(from_mob, to_mob, **opts))
        self.mentioned_from.extend(from_slot)
        self.mentioned_to.extend(to_slot)

    def _check_indices(self) -> None:
        if len(self.remaining_from) != len(self.remaining_to):
            print(  # noqa: T201
                "TransformByGlyphMap: leftover index counts differ "
                f"(from={len(self.remaining_from)}, to={len(self.remaining_to)}); "
                "switching to show_indices mode."
            )
            self.show_indices = True
            self.printing = True
        if self.printing:
            print("TransformByGlyphMap diagnostics:")  # noqa: T201
            print(f"  mentioned_from={self.mentioned_from}")  # noqa: T201
            print(f"  mentioned_to={self.mentioned_to}")  # noqa: T201
            print(f"  remaining_from ({len(self.remaining_from)})={self.remaining_from}")  # noqa: T201
            print(f"  remaining_to   ({len(self.remaining_to)})={self.remaining_to}")  # noqa: T201

    def _build_show_indices(
        self,
        a: VMobject,
        b: VMobject,
        label_height: float,
        a_color: str,
        b_color: str,
    ) -> None:
        b.next_to(a, DOWN)
        labels_a = index_labels(
            a,
            label_height=label_height,
            color=a_color,
            background_stroke_width=3,
            background_stroke_color=BLACK,
        ).set_z_index(10)
        labels_b = index_labels(
            b,
            label_height=label_height,
            color=b_color,
            background_stroke_width=3,
            background_stroke_color=BLACK,
        ).set_z_index(10)
        super().__init__(
            Create(labels_a),
            FadeIn(b, shift=DOWN),
            Create(labels_b),
            Wait(5),
            lag_ratio=0.5,
        )

    def _auto_fade(self, a: VMobject, b: VMobject) -> None:
        for i in self.remaining_from:
            self._process_entry(a, b, ([i], [], dict(self.auto_resolve_kwargs)))
        for j in self.remaining_to:
            self._process_entry(a, b, ([], [j], dict(self.auto_resolve_kwargs)))

    def _auto_morph(self, a: VMobject, b: VMobject) -> None:
        self._process_entry(
            a, b, (self.remaining_from, self.remaining_to, dict(self.auto_resolve_kwargs))
        )

    def _auto_transform(self, a: VMobject, b: VMobject) -> None:
        for i, j in zip(self.remaining_from, self.remaining_to, strict=False):
            self._process_entry(a, b, ([i], [j], dict(self.auto_resolve_kwargs)))

    def begin(self) -> None:
        self.mobA.save_state()
        super().begin()

    def clean_up_from_scene(self, scene: Any) -> None:
        self.mobA.restore()
        super().clean_up_from_scene(scene)
        # Re-attach mobB as a single parent rather than a bag of orphan submobs.
        scene.remove(self.mobB)
        scene.add(self.mobB)


class GhostSlideFade(Animation):
    """Fade a mobject in, optionally drift / scale / rotate it, then fade out.

    Self-contained: removes the mobject from the scene on cleanup, so callers
    can spawn ghost cues without later teardown bookkeeping.
    """

    def __init__(
        self,
        mob: Mobject,
        *,
        scale_factor: float = 1.0,
        shift_vector: np.ndarray = ORIGIN,
        rotate_amount: float = 0.0,
        fade_in_time: float = 1.0,
        fade_out_time: float = 1.0,
        lifetime: float = 3.0,
        living_stroke_opacity: float = 1.0,
        living_fill_opacity: float = 0.0,
        **kwargs: Any,
    ) -> None:
        self.mobject = mob
        self.scale_factor = scale_factor
        self.shift_vector = shift_vector
        self.rotate_amount = rotate_amount
        self.fade_in_time = fade_in_time
        self.fade_out_time = fade_out_time
        self.lifetime = lifetime
        self.living_stroke_opacity = living_stroke_opacity
        self.living_fill_opacity = living_fill_opacity
        kwargs.setdefault("run_time", fade_in_time + lifetime + fade_out_time)
        super().__init__(mob, **kwargs)

    def clean_up_from_scene(self, scene: Any) -> None:
        super().clean_up_from_scene(scene)
        scene.remove(self.mobject)

    def interpolate_mobject(self, alpha: float) -> None:
        alpha = self.rate_func(alpha)
        total = self.fade_in_time + self.lifetime + self.fade_out_time
        self.mobject.become(self.starting_mobject)
        self.mobject.scale(self.scale_factor**alpha)
        self.mobject.shift(self.shift_vector * alpha)
        self.mobject.rotate(self.rotate_amount * alpha, about_point=self.mobject.get_center())
        in_frac = self.fade_in_time / total
        out_frac = 1 - self.fade_out_time / total
        if alpha <= in_frac:
            factor = alpha / in_frac if in_frac > 0 else 1.0
        elif alpha >= out_frac:
            tail = self.fade_out_time / total
            factor = (1 - alpha) / tail if tail > 0 else 0.0
        else:
            factor = 1.0
        self.mobject.set_fill(opacity=self.living_fill_opacity * factor)
        self.mobject.set_stroke(opacity=self.living_stroke_opacity * factor)
