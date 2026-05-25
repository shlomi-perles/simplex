"""Fetch and verify web assets that are bundled into release wheels."""

from pathlib import Path

from simplex.web import vendor

STATIC_DIR = Path("src/simplex/web/static")

REQUIRED = (
    "tailwind.css",
    "htmx.min.js",
    "katex/katex.min.css",
    "katex/katex.min.js",
    "katex/auto-render.min.js",
    "katex/fonts/KaTeX_Main-Regular.woff2",
    "reveal.js/reveal.js",
    "reveal.js/reveal.css",
    "reveal.js/reset.css",
    "fonts/lato/lato-latin-400-normal.woff2",
    "fonts/merriweather/merriweather-latin-400-normal.woff2",
)


def main() -> int:
    vendor.ensure(STATIC_DIR)
    missing = [rel for rel in REQUIRED if not (STATIC_DIR / rel).exists()]
    if missing:
        print("Missing vendored asset(s):")
        for rel in missing:
            print(f"  - {rel}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
