"""CLI serve socket binding behavior."""

from __future__ import annotations

from pathlib import Path

import pytest
import typer

from simplex.cli import commands


def _close(server: commands._SimplexTCPServer | None) -> None:
    if server is not None:
        server.server_close()


def test_bind_server_uses_next_free_port_when_preferred_port_is_busy(tmp_path: Path) -> None:
    handler_cls = commands._make_handler(tmp_path)
    occupied = commands._bind_server("127.0.0.1", 0, handler_cls, strict_port=True)
    fallback: commands._SimplexTCPServer | None = None
    try:
        occupied_port = int(occupied.server_address[1])
        if occupied_port > 65531:
            pytest.skip("OS selected a port too close to the upper bound for fallback scan")

        fallback = commands._bind_server(
            "127.0.0.1",
            occupied_port,
            handler_cls,
            strict_port=False,
            scan_limit=4,
        )

        assert int(fallback.server_address[1]) != occupied_port
        assert int(fallback.server_address[1]) in range(occupied_port + 1, occupied_port + 4)
    finally:
        _close(fallback)
        _close(occupied)


def test_bind_server_strict_port_reports_busy_port(tmp_path: Path) -> None:
    handler_cls = commands._make_handler(tmp_path)
    occupied = commands._bind_server("127.0.0.1", 0, handler_cls, strict_port=True)
    try:
        occupied_port = int(occupied.server_address[1])
        with pytest.raises(typer.BadParameter, match=f"127.0.0.1:{occupied_port}"):
            commands._bind_server(
                "127.0.0.1",
                occupied_port,
                handler_cls,
                strict_port=True,
            )
    finally:
        _close(occupied)


def test_serve_port_candidates_reject_invalid_ports() -> None:
    with pytest.raises(typer.BadParameter, match="between 0 and 65535"):
        tuple(commands._serve_port_candidates(70000, strict_port=False))
