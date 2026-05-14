"""ContextVar-backed active theme."""

from collections.abc import Generator
from contextlib import contextmanager
from contextvars import ContextVar

from simplex.theme.tokens import Theme

_active: ContextVar[Theme | None] = ContextVar("simplex_active_theme", default=None)


@contextmanager
def active_theme(theme: Theme) -> Generator[Theme]:
    """Push `theme` onto the active stack for the duration of the with-block."""
    token = _active.set(theme)
    try:
        yield theme
    finally:
        _active.reset(token)


def get_active_theme() -> Theme:
    """Return the active theme, falling back to DASTIMATOR_DARK."""
    theme = _active.get()
    if theme is None:
        from simplex.theme.presets import DASTIMATOR_DARK

        return DASTIMATOR_DARK
    return theme
