"""Fetch vendored runtime assets (tailwind, katex, reveal.js, fonts) into the
package static dir.

Pinned versions are intentional so builds are reproducible. This is the
sole vendoring path -- called from `simplex build`; works the same on
Windows, macOS, and Linux without needing bash or Node.

Idempotent: files that already exist are not re-downloaded.

Tailwind is built locally from the v4 standalone CLI: we download the
platform-appropriate binary into a per-user cache once, then compile
``tailwind.input.css`` to ``tailwind.css`` against the package templates.
That ships a single ~10 KB minified stylesheet rather than the 410 KB
``cdn.tailwindcss.com`` runtime (which the upstream bundle explicitly
warns against using in production).

Fonts come from the ``@fontsource`` packages on jsDelivr -- stable WOFF2
URLs that ship with semver-pinned releases (unlike Google Fonts' rolling
``fonts.gstatic.com`` paths). We bundle Lato (UI / headings) and
Merriweather (body / academic notes) to match the deck-notes academic
typography stack.
"""

import os
import platform
import stat
import subprocess
import warnings
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

TAILWIND_VER = "4.3.0"
KATEX_VER = "0.16.11"
REVEAL_VER = "5.1.0"
HTMX_VER = "1.9.12"
LATO_VER = "5.0.18"
MERRIWEATHER_VER = "5.0.13"
LUCIDE_VER = "1.16.0"

_UNPKG = "https://unpkg.com"
_JSDELIVR = "https://cdn.jsdelivr.net/npm"
_TAILWIND_RELEASES = "https://github.com/tailwindlabs/tailwindcss/releases/download"

_STALE_PATHS = (
    # Reveal's `black.css` theme used to live here; it `@import`s
    # `fonts/source-sans-pro/source-sans-pro.css` which we don't vendor,
    # producing a 404. The inline <style> block in revealjs.html.j2 supplies
    # every visual we need, so we no longer ship a theme file at all.
    "reveal.js/theme/simplex.css",
    # Tailwind Play CDN runtime (v3). Replaced by a precompiled tailwind.css
    # produced from the v4 standalone CLI; keep the cleanup so upgrades from
    # an older checkout don't leave the 410 KB bundle lying around.
    "tailwind.js",
)

_KATEX_FONTS = (
    "KaTeX_Main-Regular.woff2",
    "KaTeX_Main-Bold.woff2",
    "KaTeX_Math-Italic.woff2",
    "KaTeX_Math-BoldItalic.woff2",
    "KaTeX_AMS-Regular.woff2",
    "KaTeX_Size1-Regular.woff2",
    "KaTeX_Size2-Regular.woff2",
    "KaTeX_Size3-Regular.woff2",
    "KaTeX_Size4-Regular.woff2",
)

# Per @fontsource convention: <pkg>/files/<family>-<subset>-<weight>-<style>.woff2
# Subset stays `latin` (covers ASCII + Latin-1 + the common punctuation we use).
_LATO_FACES = (
    ("400", "normal"),
    ("400", "italic"),
    ("700", "normal"),
    ("700", "italic"),
    ("900", "normal"),
)
_MERRIWEATHER_FACES = (
    ("400", "normal"),
    ("400", "italic"),
    ("700", "normal"),
    ("700", "italic"),
    ("900", "normal"),
)


def _assets() -> tuple[tuple[str, str], ...]:
    items: list[tuple[str, str]] = [
        (f"{_UNPKG}/katex@{KATEX_VER}/dist/katex.min.css", "katex/katex.min.css"),
        (f"{_UNPKG}/katex@{KATEX_VER}/dist/katex.min.js", "katex/katex.min.js"),
        (
            f"{_UNPKG}/katex@{KATEX_VER}/dist/contrib/auto-render.min.js",
            "katex/auto-render.min.js",
        ),
        (f"{_UNPKG}/reveal.js@{REVEAL_VER}/dist/reveal.js", "reveal.js/reveal.js"),
        (f"{_UNPKG}/reveal.js@{REVEAL_VER}/dist/reveal.css", "reveal.js/reveal.css"),
        (f"{_UNPKG}/reveal.js@{REVEAL_VER}/dist/reset.css", "reveal.js/reset.css"),
        (f"{_UNPKG}/htmx.org@{HTMX_VER}/dist/htmx.min.js", "htmx.min.js"),
        (f"{_UNPKG}/lucide@{LUCIDE_VER}/dist/umd/lucide.min.js", "lucide/lucide.min.js"),
    ]
    items.extend(
        (f"{_UNPKG}/katex@{KATEX_VER}/dist/fonts/{f}", f"katex/fonts/{f}") for f in _KATEX_FONTS
    )
    items.extend(_font_assets("lato", LATO_VER, _LATO_FACES))
    items.extend(_font_assets("merriweather", MERRIWEATHER_VER, _MERRIWEATHER_FACES))
    return tuple(items)


def _font_assets(
    family: str, version: str, faces: tuple[tuple[str, str], ...]
) -> list[tuple[str, str]]:
    """URLs for one ``@fontsource/<family>`` package, latin subset."""
    out: list[tuple[str, str]] = []
    for weight, style in faces:
        filename = f"{family}-latin-{weight}-{style}.woff2"
        url = f"{_JSDELIVR}/@fontsource/{family}@{version}/files/{filename}"
        out.append((url, f"fonts/{family}/{filename}"))
    return out


def _download(url: str, dest: Path) -> None:
    if not url.startswith("https://"):
        msg = f"Refusing to fetch non-https URL: {url}"
        raise ValueError(msg)
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = Request(url, headers={"User-Agent": "simplex-vendor/1.0"})  # noqa: S310
    with urlopen(req, timeout=30) as resp:  # noqa: S310
        dest.write_bytes(resp.read())


def _tailwind_binary_name() -> str | None:
    """Return the standalone CLI asset name for the current OS/arch, or None
    if no upstream binary exists (e.g. Windows on ARM)."""
    system = platform.system()
    machine = platform.machine().lower()
    if system == "Windows":
        return "tailwindcss-windows-x64.exe" if machine in {"amd64", "x86_64"} else None
    if system == "Darwin":
        if machine in {"arm64", "aarch64"}:
            return "tailwindcss-macos-arm64"
        if machine in {"x86_64", "amd64"}:
            return "tailwindcss-macos-x64"
        return None
    if system == "Linux":
        if machine in {"aarch64", "arm64"}:
            return "tailwindcss-linux-arm64"
        if machine in {"x86_64", "amd64"}:
            return "tailwindcss-linux-x64"
        return None
    return None


def _tailwind_cache_dir() -> Path:
    """Per-user cache for downloaded standalone CLI binaries (gitignored,
    shared across simplex projects on the same machine)."""
    if platform.system() == "Windows":
        base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
    else:
        base = os.environ.get("XDG_CACHE_HOME") or str(Path.home() / ".cache")
    return Path(base) / "simplex" / "tailwind" / f"v{TAILWIND_VER}"


def _ensure_tailwind_binary() -> Path | None:
    """Download the v4 standalone CLI for this platform on first use. Returns
    the path to the cached executable, or None if no binary is available."""
    name = _tailwind_binary_name()
    if name is None:
        return None
    dest = _tailwind_cache_dir() / name
    if dest.exists():
        return dest
    url = f"{_TAILWIND_RELEASES}/v{TAILWIND_VER}/{name}"
    _download(url, dest)
    if platform.system() != "Windows":
        dest.chmod(dest.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return dest


def _compile_tailwind(static_dir: Path) -> None:
    """Run the standalone CLI to produce ``tailwind.css`` from
    ``tailwind.input.css``. Sources are discovered via the ``@source``
    directives inside the input file."""
    input_css = static_dir / "tailwind.input.css"
    output_css = static_dir / "tailwind.css"
    if not input_css.exists():
        msg = f"Missing Tailwind input file: {input_css}"
        raise FileNotFoundError(msg)
    binary = _ensure_tailwind_binary()
    if binary is None:
        msg = (
            f"No Tailwind v{TAILWIND_VER} standalone binary for "
            f"{platform.system()}/{platform.machine()}; tailwind.css will not be regenerated"
        )
        raise RuntimeError(msg)
    subprocess.run(  # noqa: S603
        [str(binary), "-i", str(input_css), "-o", str(output_css), "--minify"],
        check=True,
        capture_output=True,
    )


def ensure(static_dir: Path) -> list[Path]:
    """Download any missing vendored assets into `static_dir`, then compile
    ``tailwind.css`` from the local input file.

    Returns the list of files that were newly fetched (empty on a hot cache).
    Network failures are reported as warnings rather than raised, so an
    offline build still produces HTML (just without those assets).
    """
    for rel in _STALE_PATHS:
        stale = static_dir / rel
        if stale.exists():
            stale.unlink()
    fetched: list[Path] = []
    failed: list[str] = []
    for url, rel in _assets():
        dest = static_dir / rel
        if dest.exists():
            continue
        try:
            _download(url, dest)
        except (URLError, TimeoutError, OSError) as exc:
            failed.append(f"{rel} ({exc})")
            continue
        fetched.append(dest)
    try:
        _compile_tailwind(static_dir)
    except (URLError, TimeoutError, OSError, RuntimeError, subprocess.CalledProcessError) as exc:
        detail = (
            exc.stderr.decode("utf-8", "replace")
            if isinstance(exc, subprocess.CalledProcessError)
            else str(exc)
        )
        failed.append(f"tailwind.css ({detail.strip() or exc!r})")
    else:
        css = static_dir / "tailwind.css"
        if css.exists():
            fetched.append(css)
    if failed:
        warnings.warn(
            "simplex: could not vendor "
            + str(len(failed))
            + " asset(s); page styles/scripts may be missing: "
            + "; ".join(failed),
            stacklevel=2,
        )
    return fetched
