"""Warning policy for noisy third-party render dependencies."""

from __future__ import annotations

import warnings

PYDUB_SYNTAX_WARNING_FILTER = "ignore:invalid escape sequence:SyntaxWarning:pydub.utils"


def append_pythonwarnings_filter(current: str | None) -> str:
    """Append Simplex's subprocess-only warning filters to PYTHONWARNINGS."""
    if not current:
        return PYDUB_SYNTAX_WARNING_FILTER
    return f"{current},{PYDUB_SYNTAX_WARNING_FILTER}"


def filter_pydub_syntax_warning() -> None:
    """Hide pydub's Python 3.13 invalid-escape warning without muting setup warnings."""
    warnings.filterwarnings(
        "ignore",
        message="invalid escape sequence",
        category=SyntaxWarning,
        module=r"pydub\.utils",
    )
