"""Manager subprocess entry point for Manim with ANSI-rich captured logs."""

from __future__ import annotations

import logging
import sys
from typing import Any, cast

from rich.console import Console


def _force_ansi_consoles() -> None:
    import manim._config as manim_config
    from manim._config import logger_utils

    theme = logger_utils.parse_theme(manim_config.parser["logger"])
    console = Console(
        theme=theme,
        force_terminal=True,
        color_system="truecolor",
        legacy_windows=False,
    )
    error_console = Console(
        theme=theme,
        stderr=True,
        force_terminal=True,
        color_system="truecolor",
        legacy_windows=False,
    )

    manim_config.console = console
    manim_config.error_console = error_console
    manim_module = cast(Any, sys.modules.get("manim"))
    if manim_module is not None:
        manim_module.console = console
        manim_module.error_console = error_console

    for logger_name in ("manim", ""):
        logger = logging.getLogger(logger_name)
        for handler in logger.handlers:
            handler_any = cast(Any, handler)
            if hasattr(handler_any, "console"):
                handler_any.console = console


def main() -> None:
    """Run Manim's CLI with consoles suitable for manager log capture."""
    _force_ansi_consoles()
    from manim.__main__ import main as manim_main

    manim_main(prog_name="manim")


if __name__ == "__main__":
    main()
