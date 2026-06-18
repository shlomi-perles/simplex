"""Background job execution for the Simplex manager."""

from __future__ import annotations

import os
import shutil
import signal
import subprocess
import sys
import threading
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal, cast

from simplex.deck.config import DeckConfig
from simplex.deck.registry import discover
from simplex.manager.state import (
    CacheMode,
    SlideThemeSelection,
    manim_args_for_options,
)
from simplex.render import themes
from simplex.web.site_config import SiteConfig

JobAction = Literal["render_scene", "render_deck", "build"]
JobStatus = Literal["queued", "running", "success", "failed", "cancelled"]


@dataclass(frozen=True, slots=True)
class JobRequest:
    action: JobAction
    deck_slug: str | None = None
    scene: str | None = None
    deck_slugs: tuple[str, ...] = ()
    slide_theme: SlideThemeSelection = "all"
    quality: str | None = None
    cache: CacheMode = "on"
    open_after: bool = False
    no_render: bool = False

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> JobRequest:
        action = str(data.get("action") or "")
        if action not in {"render_scene", "render_deck", "build"}:
            raise ValueError("action must be render_scene, render_deck, or build")
        slide_theme = str(data.get("slideTheme") or "all")
        if slide_theme not in {"all", "dark", "light"}:
            raise ValueError("slideTheme must be all, dark, or light")
        cache = str(data.get("cache") or "on")
        if cache not in {"on", "off", "flush"}:
            raise ValueError("cache must be on, off, or flush")
        raw_slugs = data.get("deckSlugs") or ()
        deck_slugs = tuple(str(slug) for slug in raw_slugs) if isinstance(raw_slugs, list) else ()
        return cls(
            action=action,  # type: ignore[arg-type]
            deck_slug=str(data["deckSlug"]) if data.get("deckSlug") else None,
            scene=str(data["scene"]) if data.get("scene") else None,
            deck_slugs=deck_slugs,
            slide_theme=slide_theme,  # type: ignore[arg-type]
            quality=str(data["quality"]) if data.get("quality") else None,
            cache=cache,  # type: ignore[arg-type]
            open_after=bool(data.get("openAfter")),
            no_render=bool(data.get("noRender")),
        )


@dataclass(slots=True)
class Job:
    id: str
    request: JobRequest
    command: tuple[str, ...]
    name: str
    status: JobStatus = "queued"
    returncode: int | None = None
    logs: list[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    started_at: float | None = None
    ended_at: float | None = None
    opened: str = ""
    error: str = ""
    stop_requested: bool = False
    process: subprocess.Popen[str] | None = field(default=None, repr=False, compare=False)

    def to_json(self) -> dict[str, object]:
        return {
            "id": self.id,
            "name": self.name,
            "action": self.request.action,
            "deckSlug": self.request.deck_slug,
            "scene": self.request.scene,
            "noRender": self.request.no_render,
            "command": list(self.command),
            "status": self.status,
            "returncode": self.returncode,
            "logs": self.logs[-400:],
            "createdAt": self.created_at,
            "startedAt": self.started_at,
            "endedAt": self.ended_at,
            "opened": self.opened,
            "error": self.error,
        }


class JobStore:
    """In-memory manager job store with a simple change counter."""

    def __init__(self, repo_root: Path) -> None:
        self._repo_root = repo_root
        self._jobs: dict[str, Job] = {}
        self._condition = threading.Condition()
        self._version = 0

    @property
    def version(self) -> int:
        with self._condition:
            return self._version

    def start(self, request: JobRequest) -> Job:
        command = command_for_request(self._repo_root, request)
        job = Job(
            id=uuid.uuid4().hex[:12],
            request=request,
            command=command,
            name=job_name_for_request(self._repo_root, request),
        )
        with self._condition:
            self._jobs[job.id] = job
            self._changed()
        thread = threading.Thread(target=self._run, args=(job.id,), daemon=True)
        thread.start()
        return job

    def stop(self, job_id: str) -> dict[str, object]:
        with self._condition:
            job = self._jobs.get(job_id)
            if job is None:
                raise ValueError(f"unknown job: {job_id}")
            if job.status not in {"queued", "running"}:
                return self.snapshot()
            job.stop_requested = True
            self._append_locked(job, "Stopping job...")
            process = job.process
        if process is not None:
            _terminate_process_tree(process)
        return self.snapshot()

    def open_output(self, job_id: str) -> dict[str, object]:
        with self._condition:
            job = self._jobs.get(job_id)
            if job is None:
                raise ValueError(f"unknown job: {job_id}")
        target = open_target_for_request(self._repo_root, job.request)
        if target is None:
            raise ValueError("no output found for this job yet")
        _open_path(target)
        with self._condition:
            job.opened = str(target)
            self._append_locked(job, f"Opened {target}")
            return self.snapshot()

    def clear_finished(self) -> dict[str, object]:
        with self._condition:
            self._jobs = {
                job_id: job
                for job_id, job in self._jobs.items()
                if job.status in {"queued", "running"}
            }
            self._changed()
            return self.snapshot()

    def snapshot(self) -> dict[str, object]:
        with self._condition:
            jobs = sorted(self._jobs.values(), key=lambda item: item.created_at, reverse=True)
            return {"version": self._version, "jobs": [job.to_json() for job in jobs]}

    def wait_for_change(self, version: int, *, timeout: float = 20.0) -> dict[str, object]:
        with self._condition:
            if self._version <= version:
                self._condition.wait(timeout=timeout)
            return self.snapshot()

    def _run(self, job_id: str) -> None:
        job = self._jobs[job_id]
        self._set_status(job, "running")
        self._append(job, "$ " + _shellish(job.command))
        try:
            creationflags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
            process = subprocess.Popen(  # noqa: S603
                list(job.command),
                cwd=self._repo_root,
                env=_color_env(),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
                creationflags=creationflags,
                start_new_session=os.name != "nt",
            )
            job.process = process
            if job.stop_requested:
                _terminate_process_tree(process)
            assert process.stdout is not None
            for line in process.stdout:
                self._append(job, line.rstrip("\n"))
            job.returncode = process.wait()
            job.process = None
            if job.stop_requested:
                self._set_status(job, "cancelled")
            elif job.returncode == 0:
                self._open_after_success(job)
                self._set_status(job, "success")
            else:
                job.error = f"command exited with {job.returncode}"
                self._set_status(job, "failed")
        except Exception as exc:
            job.error = str(exc)
            self._append(job, f"manager error: {exc}")
            self._set_status(job, "failed")
        finally:
            job.ended_at = time.time()
            self._notify()

    def _set_status(self, job: Job, status: JobStatus) -> None:
        job.status = status
        if status == "running":
            job.started_at = time.time()
        self._notify()

    def _append(self, job: Job, line: str) -> None:
        with self._condition:
            self._append_locked(job, line)

    def _append_locked(self, job: Job, line: str) -> None:
        job.logs.append(line)
        self._changed()

    def _notify(self) -> None:
        with self._condition:
            self._changed()

    def _changed(self) -> None:
        self._version += 1
        self._condition.notify_all()

    def _open_after_success(self, job: Job) -> None:
        if not job.request.open_after:
            return
        if not manager_opens_after_success(self._repo_root, job.request):
            return
        target = open_target_for_request(self._repo_root, job.request)
        if target is None:
            self._append(job, "No output found to open.")
            return
        _open_path(target)
        job.opened = str(target)
        self._append(job, f"Opened {target}")


def command_for_request(repo_root: Path, request: JobRequest) -> tuple[str, ...]:
    """Return the subprocess command for a manager job request."""
    base = (sys.executable, "-m", "simplex.manager.run_cli")
    if request.action == "render_scene":
        if not request.deck_slug or not request.scene:
            raise ValueError("render_scene requires deckSlug and scene")
        manim_args = manim_args_for_options(
            quality=request.quality,
            cache=request.cache,
        )
        return (
            *base,
            "render",
            f"{request.deck_slug}::{request.scene}",
            "--slide-theme",
            request.slide_theme,
            *manim_args,
        )
    if request.action == "render_deck":
        if not request.deck_slug:
            raise ValueError("render_deck requires deckSlug")
        manim_args = manim_args_for_options(quality=request.quality, cache=request.cache)
        return (
            *base,
            "render",
            request.deck_slug,
            "--slide-theme",
            request.slide_theme,
            *manim_args,
        )
    if request.action == "build":
        manim_args = (
            ()
            if request.no_render
            else manim_args_for_options(
                quality=request.quality,
                cache=request.cache,
            )
        )
        only = tuple(arg for slug in request.deck_slugs for arg in ("--only", slug))
        no_render = ("--no-render",) if request.no_render else ()
        return (
            *base,
            "build",
            *only,
            *no_render,
            "--slide-theme",
            request.slide_theme,
            *manim_args,
        )
    raise ValueError(f"unknown action {request.action!r}")


def manager_opens_after_success(repo_root: Path, request: JobRequest) -> bool:
    """Return true when the manager should open output after a successful job."""
    if not request.open_after:
        return False
    if request.action == "render_scene":
        return bool(request.deck_slug and request.scene)
    return True


def job_name_for_request(repo_root: Path, request: JobRequest) -> str:
    """Return the compact UI label for a manager job."""
    if request.action == "render_scene":
        return request.scene or "Scene"
    if request.action == "render_deck":
        if request.deck_slug:
            deck = _find_deck(repo_root, request.deck_slug)
            return deck.title or deck.slug
        return "Deck"
    if request.action == "build":
        if request.no_render:
            return "Build HTML"
        if request.deck_slugs:
            return "Build " + ", ".join(request.deck_slugs)
        return "Build"
    return request.action


def open_target_for_request(repo_root: Path, request: JobRequest) -> Path | None:
    """Return the local file/page to open after a successful job."""
    if request.action == "render_scene":
        if not request.deck_slug or not request.scene:
            return None
        return _latest_scene_output(
            repo_root, request.deck_slug, request.scene, request.slide_theme
        )
    if request.action == "render_deck" and request.deck_slug:
        path = repo_root / "site" / "decks" / request.deck_slug / "index.html"
        return path if path.exists() else None
    if request.action == "build":
        path = repo_root / "site" / "index.html"
        return path if path.exists() else None
    return None


def _latest_scene_output(
    repo_root: Path,
    slug: str,
    scene: str,
    slide_theme: SlideThemeSelection,
) -> Path | None:
    deck = _find_deck(repo_root, slug)
    site_cfg = SiteConfig.load(repo_root=repo_root)
    slide_theme_config = themes.resolve_slide_themes(deck, site_cfg.slide_themes)
    variants = (
        themes.selected_variants(slide_theme_config, slide_theme)
        if slide_theme_config.enabled
        else ("dark",)
    )
    roots = [
        repo_root / ".simplex_cache" / "decks" / deck.slug / variant / "intermediate"
        for variant in variants
    ]
    candidates: list[Path] = []
    for root in roots:
        candidates.extend(root.glob(f"videos/**/{scene}.mp4"))
        candidates.extend(root.glob(f"images/**/{scene}*.png"))
    existing = [path for path in candidates if path.exists()]
    if not existing:
        return None
    return max(existing, key=lambda path: path.stat().st_mtime)


def _find_deck(repo_root: Path, slug: str) -> DeckConfig:
    site_cfg = SiteConfig.load(repo_root=repo_root)
    registry = discover(repo_root / "decks", default_section_order=site_cfg.default_section_order)
    deck = registry.find_deck(slug)
    if deck is None:
        raise ValueError(f"unknown deck: {slug}")
    return deck


def _open_path(path: Path) -> None:
    if os.name == "nt":
        _open_path_windows(path)
        return
    opener = "open" if sys.platform == "darwin" else "xdg-open"
    subprocess.Popen([opener, str(path)])  # noqa: S603


def _open_path_windows(path: Path) -> None:
    try:
        _shell_execute_foreground(path)
    except OSError:
        os.startfile(str(path))  # type: ignore[attr-defined]  # noqa: S606


def _shell_execute_foreground(path: Path) -> None:
    import ctypes
    from ctypes import wintypes

    shell32 = ctypes.WinDLL("shell32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    user32 = ctypes.WinDLL("user32", use_last_error=True)

    class ShellExecuteInfo(ctypes.Structure):
        _fields_ = [
            ("cbSize", wintypes.DWORD),
            ("fMask", wintypes.ULONG),
            ("hwnd", wintypes.HWND),
            ("lpVerb", wintypes.LPCWSTR),
            ("lpFile", wintypes.LPCWSTR),
            ("lpParameters", wintypes.LPCWSTR),
            ("lpDirectory", wintypes.LPCWSTR),
            ("nShow", ctypes.c_int),
            ("hInstApp", wintypes.HINSTANCE),
            ("lpIDList", wintypes.LPVOID),
            ("lpClass", wintypes.LPCWSTR),
            ("hkeyClass", wintypes.HANDLE),
            ("dwHotKey", wintypes.DWORD),
            ("hIcon", wintypes.HANDLE),
            ("hProcess", wintypes.HANDLE),
        ]

    shell32.ShellExecuteExW.argtypes = [ctypes.POINTER(ShellExecuteInfo)]
    shell32.ShellExecuteExW.restype = wintypes.BOOL
    kernel32.GetProcessId.argtypes = [wintypes.HANDLE]
    kernel32.GetProcessId.restype = wintypes.DWORD
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.restype = wintypes.BOOL
    user32.WaitForInputIdle.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    user32.WaitForInputIdle.restype = wintypes.DWORD

    execute_info = ShellExecuteInfo()
    execute_info.cbSize = ctypes.sizeof(ShellExecuteInfo)
    execute_info.fMask = 0x00000040  # SEE_MASK_NOCLOSEPROCESS
    execute_info.lpVerb = "open"
    execute_info.lpFile = str(path.resolve())
    execute_info.nShow = 1  # SW_SHOWNORMAL

    if not shell32.ShellExecuteExW(ctypes.byref(execute_info)):
        raise ctypes.WinError(ctypes.get_last_error())

    focused = False
    try:
        if execute_info.hProcess:
            process_id = int(kernel32.GetProcessId(execute_info.hProcess))
            user32.WaitForInputIdle(execute_info.hProcess, 5000)
            focused = _foreground_process_window(process_id, user32, kernel32)
        if not focused:
            _foreground_window_by_title(path.stem, user32, kernel32)
    finally:
        if execute_info.hProcess:
            kernel32.CloseHandle(execute_info.hProcess)


def _foreground_process_window(process_id: int, user32: object, kernel32: object) -> bool:
    import ctypes
    from ctypes import wintypes

    user32_typed = cast(Any, user32)
    kernel32_typed = cast(Any, kernel32)
    user32_typed.EnumWindows.argtypes = [
        ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM),
        wintypes.LPARAM,
    ]
    user32_typed.EnumWindows.restype = wintypes.BOOL
    user32_typed.IsWindowVisible.argtypes = [wintypes.HWND]
    user32_typed.IsWindowVisible.restype = wintypes.BOOL
    user32_typed.GetWindowThreadProcessId.argtypes = [
        wintypes.HWND,
        ctypes.POINTER(wintypes.DWORD),
    ]
    user32_typed.GetWindowThreadProcessId.restype = wintypes.DWORD
    user32_typed.GetForegroundWindow.argtypes = []
    user32_typed.GetForegroundWindow.restype = wintypes.HWND
    user32_typed.ShowWindowAsync.argtypes = [wintypes.HWND, ctypes.c_int]
    user32_typed.ShowWindowAsync.restype = wintypes.BOOL
    user32_typed.BringWindowToTop.argtypes = [wintypes.HWND]
    user32_typed.BringWindowToTop.restype = wintypes.BOOL
    user32_typed.SetForegroundWindow.argtypes = [wintypes.HWND]
    user32_typed.SetForegroundWindow.restype = wintypes.BOOL
    user32_typed.AttachThreadInput.argtypes = [wintypes.DWORD, wintypes.DWORD, wintypes.BOOL]
    user32_typed.AttachThreadInput.restype = wintypes.BOOL
    user32_typed.keybd_event.argtypes = [
        wintypes.BYTE,
        wintypes.BYTE,
        wintypes.DWORD,
        wintypes.ULONG,
    ]
    user32_typed.keybd_event.restype = None
    kernel32_typed.GetCurrentThreadId.argtypes = []
    kernel32_typed.GetCurrentThreadId.restype = wintypes.DWORD

    enum_proc_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    deadline = time.monotonic() + 8.0
    while time.monotonic() < deadline:
        hwnd = _find_process_window(process_id, user32_typed, enum_proc_type)
        if hwnd is not None:
            _raise_window(hwnd, user32_typed, kernel32_typed)
            return True
        time.sleep(0.15)
    return False


def _foreground_window_by_title(stem: str, user32: object, kernel32: object) -> bool:
    import ctypes
    from ctypes import wintypes

    user32_typed = cast(Any, user32)
    kernel32_typed = cast(Any, kernel32)
    user32_typed.EnumWindows.argtypes = [
        ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM),
        wintypes.LPARAM,
    ]
    user32_typed.EnumWindows.restype = wintypes.BOOL
    user32_typed.IsWindowVisible.argtypes = [wintypes.HWND]
    user32_typed.IsWindowVisible.restype = wintypes.BOOL
    user32_typed.GetWindowTextLengthW.argtypes = [wintypes.HWND]
    user32_typed.GetWindowTextLengthW.restype = ctypes.c_int
    user32_typed.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    user32_typed.GetWindowTextW.restype = ctypes.c_int

    enum_proc_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    deadline = time.monotonic() + 8.0
    needle = stem.casefold()
    while time.monotonic() < deadline:
        hwnd = _find_window_by_title(needle, user32_typed, enum_proc_type)
        if hwnd is not None:
            _raise_window(hwnd, user32_typed, kernel32_typed)
            return True
        time.sleep(0.15)
    return False


def _find_process_window(process_id: int, user32: Any, enum_proc_type: Any) -> int | None:
    import ctypes
    from ctypes import wintypes

    found: list[int] = []

    @enum_proc_type
    def enum_proc(hwnd: int, _lparam: int) -> int:
        if not user32.IsWindowVisible(hwnd):
            return 1
        window_pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(window_pid))
        if int(window_pid.value) == process_id:
            found.append(hwnd)
            return 0
        return 1

    user32.EnumWindows(enum_proc, 0)
    return found[0] if found else None


def _find_window_by_title(needle: str, user32: Any, enum_proc_type: Any) -> int | None:
    import ctypes

    found: list[int] = []

    @enum_proc_type
    def enum_proc(hwnd: int, _lparam: int) -> int:
        if not user32.IsWindowVisible(hwnd):
            return 1
        length = int(user32.GetWindowTextLengthW(hwnd))
        if length <= 0:
            return 1
        buffer = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buffer, length + 1)
        if needle in buffer.value.casefold():
            found.append(hwnd)
            return 0
        return 1

    user32.EnumWindows(enum_proc, 0)
    return found[0] if found else None


def _raise_window(hwnd: int, user32: Any, kernel32: Any) -> None:
    sw_restore = 9
    vk_menu = 0x12
    keyeventf_keyup = 0x0002
    current_thread = kernel32.GetCurrentThreadId()
    target_thread = user32.GetWindowThreadProcessId(hwnd, None)
    foreground = user32.GetForegroundWindow()
    foreground_thread = user32.GetWindowThreadProcessId(foreground, None) if foreground else 0

    if target_thread:
        user32.AttachThreadInput(current_thread, target_thread, True)
    if foreground_thread and foreground_thread != target_thread:
        user32.AttachThreadInput(foreground_thread, target_thread, True)
    try:
        user32.ShowWindowAsync(hwnd, sw_restore)
        user32.keybd_event(vk_menu, 0, 0, 0)
        user32.keybd_event(vk_menu, 0, keyeventf_keyup, 0)
        user32.BringWindowToTop(hwnd)
        user32.SetForegroundWindow(hwnd)
    finally:
        if foreground_thread and foreground_thread != target_thread:
            user32.AttachThreadInput(foreground_thread, target_thread, False)
        if target_thread:
            user32.AttachThreadInput(current_thread, target_thread, False)


def _color_env() -> dict[str, str]:
    env = os.environ.copy()
    env["FORCE_COLOR"] = "1"
    env["CLICOLOR_FORCE"] = "1"
    env["PY_COLORS"] = "1"
    env["PYTHONUNBUFFERED"] = "1"
    env["SIMPLEX_MANAGER_FORCE_ANSI"] = "1"
    env["TTY_COMPATIBLE"] = "1"
    env["TTY_INTERACTIVE"] = "0"
    env.setdefault("TERM", "xterm-256color")
    return env


def _terminate_process_tree(process: subprocess.Popen[str]) -> None:
    if process.poll() is not None:
        return
    if os.name == "nt":
        taskkill = shutil.which("taskkill")
        if taskkill is None:
            process.terminate()
            return
        subprocess.run(  # noqa: S603
            [taskkill, "/PID", str(process.pid), "/T", "/F"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        return
    killpg = getattr(os, "killpg", None)
    if not callable(killpg):
        process.terminate()
        return
    try:
        killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    except OSError:
        process.terminate()


def _shellish(command: tuple[str, ...]) -> str:
    return " ".join(_quote(part) for part in command)


def _quote(value: str) -> str:
    if not value or any(ch.isspace() for ch in value):
        return '"' + value.replace('"', '\\"') + '"'
    return value
