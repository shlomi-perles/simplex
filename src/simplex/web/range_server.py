"""HTTP byte-range support for local Simplex static serving."""

from __future__ import annotations

import http.server
from pathlib import Path
from typing import Any, BinaryIO


class RangeRequestHandlerMixin(http.server.SimpleHTTPRequestHandler):
    """Mixin for ``SimpleHTTPRequestHandler`` subclasses.

    Chromium and Safari need byte ranges for reliable MP4 seeking. Most static
    hosts provide them; this mixin gives the local dev server the same behavior.
    """

    _range_remaining: int | None = None

    def end_headers(self) -> None:
        self.send_header("Accept-Ranges", "bytes")
        super().end_headers()  # type: ignore[misc]

    def send_head(self) -> BinaryIO | None:
        range_header = self.headers.get("Range")
        if not range_header:
            self._range_remaining = None
            return super().send_head()  # type: ignore[misc]

        path = Path(self.translate_path(self.path))  # type: ignore[attr-defined]
        if path.is_dir() or not path.is_file():
            self._range_remaining = None
            return super().send_head()  # type: ignore[misc]

        try:
            file = path.open("rb")
        except OSError:
            self.send_error(404, "File not found")  # type: ignore[attr-defined]
            return None

        size = path.stat().st_size
        byte_range = _parse_range(range_header, size)
        if byte_range is None:
            file.close()
            self.send_error(416, "Requested Range Not Satisfiable")  # type: ignore[attr-defined]
            return None

        start, end = byte_range
        length = end - start + 1
        file.seek(start)
        self._range_remaining = length
        self.send_response(206)  # type: ignore[attr-defined]
        self.send_header("Content-type", self.guess_type(str(path)))  # type: ignore[attr-defined]
        self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.send_header("Content-Length", str(length))
        self.send_header("Last-Modified", self.date_time_string(path.stat().st_mtime))  # type: ignore[attr-defined]
        self.end_headers()
        return file

    def copyfile(self, source: Any, outputfile: Any) -> None:
        remaining = self._range_remaining
        if remaining is None:
            super().copyfile(source, outputfile)  # type: ignore[misc]
            return
        try:
            while remaining > 0:
                chunk = source.read(min(64 * 1024, remaining))
                if not chunk:
                    break
                outputfile.write(chunk)
                remaining -= len(chunk)
        finally:
            self._range_remaining = None


def _parse_range(header: str, size: int) -> tuple[int, int] | None:
    if size <= 0 or not header.startswith("bytes="):
        return None
    spec = header.removeprefix("bytes=").split(",", 1)[0].strip()
    start_text, separator, end_text = spec.partition("-")
    if not separator:
        return None
    try:
        if start_text:
            start = int(start_text)
            end = int(end_text) if end_text else size - 1
        else:
            suffix = int(end_text)
            if suffix <= 0:
                return None
            start = max(0, size - suffix)
            end = size - 1
    except ValueError:
        return None
    if start < 0 or start >= size:
        return None
    end = min(end, size - 1)
    if end < start:
        return None
    return start, end
