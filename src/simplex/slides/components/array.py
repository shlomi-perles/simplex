"""ArrayMob, ArrayEntry, ArrayPointer -- ported and cleaned from Dastimator.

Vanilla Manim mobjects. No factories; no wrapping. Authors construct directly::

    arr = ArrayMob(\"A:\", \"-\", \"8\", \"1\", \"3\", show_indices=True, starting_index=1)
    self.play(Write(arr))
    self.play(arr.animate.at(1, \"b\"))  # `.at` is sync; wrap in `.animate` to animate.
    self.play(arr.indicate_at(1))
    self.play(arr.push(\"5\"))
    self.play(arr.swap(1, 3))
"""

from typing import Any, cast

import numpy as np
from manim import (
    DEFAULT_FONT_SIZE,
    DOWN,
    LEFT,
    ORIGIN,
    RIGHT,
    TAU,
    UP,
    Animation,
    AnimationGroup,
    ArcBetweenPoints,
    FadeIn,
    FadeOut,
    Indicate,
    MathTex,
    Mobject,
    MoveAlongPath,
    Square,
    Tex,
    Text,
    Vector,
    VGroup,
    VMobject,
)

from simplex.theme.context import get_active_theme

_DEFAULT_CHAR = "-"
_VALUE_HEIGHT_FRACTION = 0.65
_INDEX_HEIGHT_FRACTION = 0.18
_INDEX_BUFF = 0.12


def _is_blank(x: Any) -> bool:
    return x is None or x == ""


class ArrayEntry(VGroup):
    """One cell of an ArrayMob: a frame + value + optional index label."""

    def __init__(
        self,
        value: float | str,
        index: int | str | Tex | MathTex | Text,
        *,
        index_scale: float = 1.0,
        frame_type: type[VMobject] = Square,
        index_pos: np.ndarray | None = None,
        frame_config: dict[str, Any] | None = None,
        value_config: dict[str, Any] | None = None,
        index_config: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.value = value
        self.index = index
        self.index_scale = index_scale
        self.frame_type = frame_type
        self.index_pos = np.array(DOWN) if index_pos is None else np.copy(index_pos)
        self.frame_config = frame_config or {}
        self.value_config = value_config or {}
        self.index_config = index_config or {}

        self.frame: VMobject = self.frame_type(**self.frame_config)
        self.value_mob: VMobject = self._make_label(self.value, self.value_config)
        self.index_mob: VMobject = (
            self.index
            if isinstance(self.index, (Tex, MathTex, Text))
            else self._make_label(self.index, self.index_config)
        )

        if _is_blank(self.value):
            self.value_mob.set_opacity(0).scale(0.2)
        if _is_blank(self.index):
            self.index_mob.set_opacity(0).scale(0.2)

        self._place_value()
        if self.index:
            self._place_index()
        self.add(self.frame, self.value_mob, self.index_mob)

    @staticmethod
    def _make_label(content: Any, config: dict[str, Any]) -> Tex:
        return Tex(_DEFAULT_CHAR if _is_blank(content) else str(content), **config)

    def _place_value(self) -> ArrayEntry:
        self.value_mob.move_to(self.frame)
        target = self.frame.height * _VALUE_HEIGHT_FRACTION
        if self.value_mob.width < self.value_mob.height:
            self.value_mob.scale_to_fit_height(target)
        else:
            self.value_mob.scale_to_fit_width(target)
        if _is_blank(self.value):
            self.value_mob.scale(0.1)
        return self

    def _place_index(self) -> ArrayEntry:
        self.index_mob.scale_to_fit_height(
            self.frame.height * _INDEX_HEIGHT_FRACTION * self.index_scale,
        )
        self.index_mob.next_to(
            self.frame,
            self.index_pos,
            buff=-(self.index_mob.height + _INDEX_BUFF),
        )
        self.index_mob.align_to(self.frame, RIGHT).shift(LEFT * _INDEX_BUFF)
        return self

    def set_value(self, value: float | str) -> ArrayEntry:
        self.value = value
        self.value_mob.become(self._make_label(value, self.value_config))
        if _is_blank(value):
            self.value_mob.set_opacity(0).scale(0.2)
        self._place_value()
        return self

    def set_index(self, index: int | str | Tex | MathTex | Text) -> ArrayEntry:
        self.index = index
        new = (
            index
            if isinstance(index, (Tex, MathTex, Text))
            else self._make_label(index, self.index_config)
        )
        self.index_mob.become(new)
        if _is_blank(index):
            self.index_mob.set_opacity(0).scale(0.2)
        self._place_index()
        return self


class ArrayMob(VGroup):
    """A named horizontal array of cells with animation helpers.

    Indices are author-facing (start at ``starting_index``). Internal storage
    is dense -- ``get_entry(i)`` translates to ``self.entries[i - starting_index]``.
    """

    def __init__(
        self,
        name: str,
        *values: Any,
        name_config: dict[str, Any] | None = None,
        name_scale: float = 1.0,
        show_indices: bool = False,
        indices_pos: np.ndarray | None = None,
        indices_scale: float = 1.0,
        starting_index: int = 0,
        align_point: np.ndarray | None = None,
        frame_config: dict[str, Any] | None = None,
        value_config: dict[str, Any] | None = None,
        indices_config: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.array_name = name
        self.values = values
        self.name_config = name_config or {}
        self.name_scale = name_scale
        self.show_indices = show_indices
        self.indices_pos = np.array(UP) if indices_pos is None else np.copy(indices_pos)
        self.indices_scale = indices_scale
        self.starting_index = starting_index
        self.align_point = np.array(ORIGIN) if align_point is None else np.copy(align_point)
        self._entry_kwargs: dict[str, Any] = {
            "frame_config": frame_config or {},
            "value_config": value_config or {},
            "index_config": indices_config or {},
        }

        self.entries: VGroup = VGroup()
        self.name_mob: Tex
        self.reference_entry: ArrayEntry
        self._build()
        self.center()

    def _build(self) -> None:
        name_font = 3.5 * DEFAULT_FONT_SIZE * self.name_scale
        self.name_mob = Tex(self.array_name, font_size=name_font, **self.name_config)
        self.reference_entry = ArrayEntry(0, 0, **self._entry_kwargs).set_opacity(0)
        self.add(VGroup(self.name_mob, self.reference_entry))

        for idx, val in enumerate(self.values, start=self.starting_index):
            self.entries += ArrayEntry(
                val,
                idx if self.show_indices else "",
                index_scale=self.indices_scale,
                index_pos=self.indices_pos,
                **self._entry_kwargs,
            )
        self.entries.arrange(buff=0)
        self.add(*self.entries)

        self.name_mob.next_to(self.align_point, LEFT, buff=0)
        self.entries.next_to(self.name_mob, RIGHT, buff=0.5)
        self.reference_entry.move_to(self.entries[0])

    def get_entry(self, index: int) -> ArrayEntry:
        return cast(ArrayEntry, self.entries[index - self.starting_index])

    def at(self, index: int, value: float | str) -> ArrayEntry:
        """Synchronously update one cell's value (returns the entry; not an animation)."""
        return self.get_entry(index).set_value(value)

    def indicate_at(
        self,
        index: int,
        *,
        color: str | None = None,
        preserve_color: bool = True,
        **kwargs: Any,
    ) -> AnimationGroup:
        theme = get_active_theme()
        color = color or theme.palette.accent
        entry = self.get_entry(index)
        if preserve_color:
            entry.set_color(color)
        entry.set_z_index(self.get_z_index() + 1)
        return AnimationGroup(Indicate(entry, **kwargs))

    def push(
        self,
        value: int | str,
        *,
        side: np.ndarray = RIGHT,
        **kwargs: Any,
    ) -> Animation:
        side = np.array(side)
        new_entry = ArrayEntry(
            value,
            len(self.entries) + self.starting_index if self.show_indices else "",
            index_scale=self.indices_scale,
            index_pos=self.indices_pos,
            **self._entry_kwargs,
        ).match_height(self.reference_entry)

        if len(self.entries) == 0 or np.allclose(side, LEFT):
            new_entry.move_to(self.reference_entry)
        else:
            new_entry.next_to(self.entries[-1], side, buff=0)

        if np.allclose(side, LEFT):
            self.entries.insert(0, new_entry)
            self.add(new_entry)
            tail = cast(VGroup, self.entries[1:])
            return AnimationGroup(
                FadeIn(new_entry, shift=-side, **kwargs),
                cast(Animation, tail.animate.next_to(self.reference_entry, RIGHT, buff=0)),
            )
        self.entries.add(new_entry)
        self.add(new_entry)
        return FadeIn(new_entry, shift=-side, **kwargs)

    def pop(
        self,
        index: int | None = None,
        *,
        shift: np.ndarray = DOWN,
        **kwargs: Any,
    ) -> AnimationGroup:
        index = len(self.entries) + self.starting_index - 1 if index is None else index
        kwargs.setdefault("lag_ratio", 1)

        target = self.get_entry(index)
        anims: list[Animation] = [FadeOut(target, shift=shift)]
        self.remove(target)
        self.entries.remove(target)

        if len(self.entries) == 0:
            return AnimationGroup(*anims, **kwargs)

        tail = cast(VGroup, self.entries[index - self.starting_index :])
        remaining = VGroup(*tail)
        if len(remaining) > 0:
            anchor: Mobject = (
                self.get_entry(index - 1) if index != self.starting_index else self.reference_entry
            )
            anims.append(cast(Animation, remaining.animate.next_to(anchor, RIGHT, buff=0)))
        return AnimationGroup(*anims, **kwargs)

    def swap(
        self,
        i: int,
        j: int,
        *,
        arc_angle: float = TAU / 3,
        **kwargs: Any,
    ) -> AnimationGroup:
        if i > j:
            i, j = j, i
        entry_i = self.get_entry(i)
        entry_j = self.get_entry(j)
        right_path = ArcBetweenPoints(
            entry_i.get_center(),
            entry_j.get_center(),
            angle=arc_angle,
        )
        left_path = ArcBetweenPoints(
            entry_j.get_center(),
            entry_i.get_center(),
            angle=arc_angle,
        )
        anim = AnimationGroup(
            MoveAlongPath(entry_i, right_path),
            MoveAlongPath(entry_j, left_path),
            **kwargs,
        )
        a, b = i - self.starting_index, j - self.starting_index
        subs = self.entries.submobjects
        subs[a], subs[b] = subs[b], subs[a]
        return anim


class ArrayPointer(Vector):
    """An arrow pointing at an ArrayMob entry, with an optional caption.

    Animate moves between entries via ``pointer.to_entry(new_index)``.
    """

    def __init__(
        self,
        array: ArrayMob,
        index: int,
        text: str | Mobject | None = None,
        *,
        text_scale: float = 0.6,
        direction: np.ndarray | None = None,
        change_value_color: bool = True,
        value_color: str | None = None,
        text_config: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        theme = get_active_theme()
        arrow_color: str = kwargs.setdefault("color", theme.palette.accent)
        direction = np.array(DOWN) if direction is None else np.copy(direction)
        super().__init__(direction, **kwargs)

        self.array = array
        self.index = index
        self.arrow = self[0]
        self.change_value_color = change_value_color
        self.value_color = value_color or arrow_color
        self.text_scale = text_scale
        self.text_config = text_config or {}
        self._base_z = array.get_z_index()
        array.get_entry(index).set_z_index(self._base_z + 1)
        self._position_arrow()
        self.text_mob = self._make_text(text)
        self.add(self.text_mob)

    def _make_text(self, text: str | Mobject | None) -> Mobject:
        if _is_blank(text):
            return Text(".").set_opacity(0)
        mob: Mobject = text if isinstance(text, Mobject) else MathTex(str(text), **self.text_config)
        mob.scale(self.text_scale)
        mob.next_to(self.arrow, direction=-self.get_vector(), buff=0.1)
        mob.set_color(self.get_color())
        return mob

    def _position_arrow(self) -> ArrayPointer:
        return self.next_to(
            self.array.get_entry(self.index),
            direction=-self.get_vector(),
        )

    def to_entry(
        self,
        index: int,
        *,
        text: str | Mobject | None = None,
        **kwargs: Any,
    ) -> AnimationGroup:
        anims: list[Animation] = []
        if self.change_value_color:
            prev_entry = self.array.get_entry(self.index)
            new_entry = self.array.get_entry(index)
            reset_color = self.array.reference_entry.value_mob.get_color()
            anims.append(
                cast(
                    Animation, prev_entry.animate.set_color(reset_color).set_z_index(self._base_z)
                ),
            )
            anims.append(
                cast(
                    Animation,
                    new_entry.animate.set_color(self.value_color).set_z_index(self._base_z + 1),
                ),
            )
        self.index = index
        if text is not None:
            anims.append(cast(Animation, self.text_mob.animate.become(self._make_text(text))))
        return AnimationGroup(*anims, cast(Animation, self.animate._position_arrow()), **kwargs)
