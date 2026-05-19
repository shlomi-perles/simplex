"""Fetch vendored runtime assets (tailwind, katex, reveal.js, fonts) into the
package static dir.

Pinned versions are intentional so builds are reproducible. Mirrors
`scripts/vendor.sh` so Windows users (or anyone without bash) get the same
assets via plain `uv run simplex build`.

Idempotent: files that already exist are not re-downloaded.

Fonts come from the ``@fontsource`` packages on jsDelivr -- stable WOFF2
URLs that ship with semver-pinned releases (unlike Google Fonts' rolling
``fonts.gstatic.com`` paths). We bundle Lato (UI / headings) and
Merriweather (body / academic notes) to match the deck-notes academic
typography stack.
"""

import warnings
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

TAILWIND_VER = "3.4.4"
KATEX_VER = "0.16.11"
REVEAL_VER = "5.1.0"
HTMX_VER = "1.9.12"
LATO_VER = "5.0.18"
MERRIWEATHER_VER = "5.0.13"
LUCIDE_VER = "1.16.0"

_UNPKG = "https://unpkg.com"
_JSDELIVR = "https://cdn.jsdelivr.net/npm"
_TAILWIND_CDN = "https://cdn.tailwindcss.com"

_STALE_PATHS = (
    # Reveal's `black.css` theme used to live here; it `@import`s
    # `fonts/source-sans-pro/source-sans-pro.css` which we don't vendor,
    # producing a 404. The inline <style> block in revealjs.html.j2 supplies
    # every visual we need, so we no longer ship a theme file at all.
    "reveal.js/theme/simplex.css",
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
        (f"{_TAILWIND_CDN}/{TAILWIND_VER}", "tailwind.js"),
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


def ensure(static_dir: Path) -> list[Path]:
    """Download any missing vendored assets into `static_dir`.

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
    if failed:
        warnings.warn(
            "simplex: could not vendor "
            + str(len(failed))
            + " asset(s); page styles/scripts may be missing: "
            + "; ".join(failed),
            stacklevel=2,
        )
    return fetched
