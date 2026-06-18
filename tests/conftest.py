"""Shared pytest hooks for the Simplex test suite."""

import os
from pathlib import Path
from typing import Any

import pytest


@pytest.hookimpl(tryfirst=True)
def pytest_sessionfinish(session: Any, exitstatus: int) -> None:
    """Avoid Windows reparse-point errors in pytest's temp-dir cleanup."""
    del exitstatus
    if os.name != "nt":
        return

    tmp_path_factory = getattr(session.config, "_tmp_path_factory", None)
    if tmp_path_factory is None:
        return

    basetemp = Path(tmp_path_factory.getbasetemp())
    current_links = (*basetemp.glob("*current"), *basetemp.parent.glob("*current"))
    for current in current_links:
        try:
            if current.is_symlink():
                current.unlink()
        except OSError:
            continue
