"""Title-style hero slides."""

from manim import DOWN, Tex

from simplex.slides.base import BaseSlide
from simplex.theme.context import get_active_theme


class TitleSlide(BaseSlide):
    """A centered title with an optional subtitle."""

    title: str = ""
    subtitle: str = ""

    def construct(self) -> None:
        theme = get_active_theme()
        title_mob = Tex(self.title, font_size=theme.typography.h1)
        self.region.place(title_mob, "center")
        if self.subtitle:
            sub = Tex(self.subtitle, font_size=theme.typography.h2)
            sub.next_to(title_mob, DOWN, buff=0.4)
            self.add(title_mob, sub)
        else:
            self.add(title_mob)
        self.next_slide()


class SectionDivider(BaseSlide):
    """A section break: one big label, centered."""

    label: str = ""

    def construct(self) -> None:
        theme = get_active_theme()
        mob = Tex(self.label, font_size=theme.typography.h1)
        self.region.place(mob, "center")
        self.add(mob)
        self.next_slide()
