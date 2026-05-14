"""Content slides with header / footer / page number chrome."""

from manim import Tex

from simplex.slides.base import BaseSlide
from simplex.theme.context import get_active_theme
from simplex.theme.tokens import Theme


class ContentSlide(BaseSlide):
    """Body-content slide that reserves chrome space inside `self.region`."""

    header: str = ""
    footer: str = ""
    page_number: int | None = None

    def setup(self) -> None:
        super().setup()
        theme = get_active_theme()
        self._add_chrome(theme)
        self.region.shrink(
            top=theme.spacing.header_height,
            bottom=theme.spacing.footer_height,
        )

    def _add_chrome(self, theme: Theme) -> None:
        if self.header:
            mob = Tex(self.header, font_size=theme.typography.h2)
            self.region.place(mob, "top", buff=0.15)
            self.add(mob)
        if self.footer:
            mob = Tex(self.footer, font_size=theme.typography.caption)
            self.region.place(mob, "bottom-left", buff=0.2)
            self.add(mob)
        if self.page_number is not None:
            mob = Tex(str(self.page_number), font_size=theme.typography.caption)
            self.region.place(mob, "bottom-right", buff=0.2)
            self.add(mob)
