"""Local HTTP server for the Simplex manager."""

from __future__ import annotations

import contextlib
import errno
import http.server
import ipaddress
import json
import mimetypes
import socketserver
import webbrowser
from collections.abc import Iterable
from importlib import resources
from pathlib import Path
from typing import Any, cast
from urllib.parse import unquote, urlparse

from rich.console import Console

from simplex.manager.jobs import JobRequest, JobStore
from simplex.manager.state import load_manager_state, update_deck_defaults, update_deck_entrypoints

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8070
PORT_SCAN_LIMIT = 100
console = Console()


class _ManagerTCPServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = False
    daemon_threads = True


def serve(
    *,
    repo_root: Path,
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    strict_port: bool = False,
    open_browser: bool = True,
) -> None:
    """Serve the local manager until interrupted."""
    store = JobStore(repo_root.resolve())
    handler_cls = _make_handler(repo_root.resolve(), store)
    server = _bind_server(host, port, handler_cls, strict_port=strict_port)
    actual_port = int(server.server_address[1])
    url = f"http://{_display_host(host)}:{actual_port}/"
    console.print(f"Simplex manager: {url}")
    if open_browser:
        webbrowser.open(url)
    try:
        server.serve_forever(poll_interval=0.2)
    except KeyboardInterrupt:
        console.print("\nStopping Simplex manager")
    finally:
        server.server_close()


def _make_handler(repo_root: Path, store: JobStore) -> type[http.server.BaseHTTPRequestHandler]:
    class _Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            path = urlparse(self.path).path
            if path == "/":
                self._send_static("index.html")
            elif path.startswith("/static/"):
                self._send_static(path.removeprefix("/static/"))
            elif path.startswith("/vendor/"):
                self._send_vendor(path.removeprefix("/vendor/"))
            elif path == "/api/state":
                self._send_json(load_manager_state(repo_root))
            elif path == "/api/jobs":
                self._send_json(store.snapshot())
            elif path == "/api/events":
                self._stream_events()
            else:
                self.send_error(404)

        def do_POST(self) -> None:
            path = urlparse(self.path).path
            try:
                if path == "/api/jobs/clear":
                    self._send_json(store.clear_finished())
                    return
                if path.startswith("/api/jobs/") and path.endswith("/stop"):
                    job_id = unquote(path.removeprefix("/api/jobs/").removesuffix("/stop"))
                    self._send_json(store.stop(job_id))
                    return
                if path.startswith("/api/jobs/") and path.endswith("/open"):
                    job_id = unquote(path.removeprefix("/api/jobs/").removesuffix("/open"))
                    self._send_json(store.open_output(job_id))
                    return
                if path.startswith("/api/decks/") and path.endswith("/entrypoints"):
                    slug = unquote(path.removeprefix("/api/decks/").removesuffix("/entrypoints"))
                    payload = self._read_json()
                    raw = payload.get("entrypoints")
                    if not isinstance(raw, list) or not all(isinstance(item, str) for item in raw):
                        raise ValueError("entrypoints must be a list of strings")
                    update_deck_entrypoints(repo_root, slug, tuple(raw))
                    self._send_json(load_manager_state(repo_root))
                    return
                if path.startswith("/api/decks/") and path.endswith("/defaults"):
                    slug = unquote(path.removeprefix("/api/decks/").removesuffix("/defaults"))
                    payload = self._read_json()
                    raw_values = payload.get("values")
                    if not isinstance(raw_values, dict):
                        raise ValueError("values must be an object")
                    values = {str(key): value for key, value in raw_values.items()}
                    update_deck_defaults(repo_root, slug, values)
                    self._send_json(load_manager_state(repo_root))
                    return
                if path == "/api/jobs":
                    request = JobRequest.from_json(self._read_json())
                    job = store.start(request)
                    self._send_json({"job": job.to_json(), **store.snapshot()}, status=202)
                    return
                self.send_error(404)
            except Exception as exc:
                self._send_json({"error": str(exc)}, status=400)

        def _read_json(self) -> dict[str, Any]:
            length = int(self.headers.get("Content-Length") or "0")
            body = self.rfile.read(length).decode("utf-8")
            data = json.loads(body or "{}")
            if not isinstance(data, dict):
                raise ValueError("expected JSON object")
            return data

        def _send_json(self, data: object, *, status: int = 200) -> None:
            body = json.dumps(data, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _send_static(self, name: str) -> None:
            clean = name.strip("/") or "index.html"
            base = resources.files("simplex.manager").joinpath("static")
            target = base.joinpath(clean)
            if not target.is_file():
                self.send_error(404)
                return
            data = target.read_bytes()
            self._send_bytes(data, _content_type(clean))

        def _send_vendor(self, name: str) -> None:
            clean = name.strip("/")
            base = resources.files("simplex.web").joinpath("static")
            target = base.joinpath(clean)
            if not target.is_file():
                self.send_error(404)
                return
            data = target.read_bytes()
            self._send_bytes(data, _content_type(clean))

        def _send_bytes(self, data: bytes, content_type: str) -> None:
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def _stream_events(self) -> None:
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.end_headers()
            version = store.version
            try:
                initial = store.snapshot()
                self.wfile.write(
                    f"event: jobs\ndata: {json.dumps(initial, ensure_ascii=False)}\n\n".encode()
                )
                self.wfile.flush()
                while True:
                    snapshot = store.wait_for_change(version, timeout=20)
                    version = int(cast(int, snapshot["version"]))
                    data = json.dumps(snapshot, ensure_ascii=False)
                    self.wfile.write(f"event: jobs\ndata: {data}\n\n".encode())
                    self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError):
                return

        def log_message(self, format: str, *args: object) -> None:
            pass

    return _Handler


def _serve_port_candidates(
    port: int,
    *,
    strict_port: bool,
    scan_limit: int = PORT_SCAN_LIMIT,
) -> Iterable[int]:
    if port < 0 or port > 65535:
        raise ValueError("port must be between 0 and 65535")
    if port == 0 or strict_port:
        return (port,)
    stop = min(65535, port + max(1, scan_limit) - 1)
    return range(port, stop + 1)


def _bind_server(
    host: str,
    port: int,
    handler_cls: type[http.server.BaseHTTPRequestHandler],
    *,
    strict_port: bool,
    scan_limit: int = PORT_SCAN_LIMIT,
) -> _ManagerTCPServer:
    last_error: OSError | None = None
    for candidate in _serve_port_candidates(port, strict_port=strict_port, scan_limit=scan_limit):
        try:
            return _ManagerTCPServer((host, candidate), handler_cls)
        except OSError as exc:
            last_error = exc
            if strict_port or port == 0 or not _is_address_in_use(exc):
                break
    detail = f": {last_error}" if last_error is not None else ""
    raise ValueError(f"could not bind {host}:{port}{detail}")


def _is_address_in_use(exc: OSError) -> bool:
    busy_errnos = {errno.EADDRINUSE}
    wsa_busy = getattr(errno, "WSAEADDRINUSE", None)
    if wsa_busy is not None:
        busy_errnos.add(wsa_busy)
    return exc.errno in busy_errnos


def _display_host(host: str) -> str:
    if not host:
        return "localhost"
    with contextlib.suppress(ValueError):
        if ipaddress.ip_address(host).is_unspecified:
            return "localhost"
    return host


def _content_type(path: str) -> str:
    guessed, _encoding = mimetypes.guess_type(path)
    if guessed:
        return guessed
    if path.endswith(".js"):
        return "text/javascript"
    return "application/octet-stream"
