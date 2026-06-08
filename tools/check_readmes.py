"""Pre-commit check: every directory under tracked roots has a README <= 100 lines."""

import sys
from pathlib import Path

ROOTS: tuple[Path, ...] = (Path("src/simplex"), Path("decks"), Path("tests"))
LIMIT: int = 100

# Runtime-generated directories under `web/static/` (populated by
# `simplex.web.vendor.ensure`). They're gitignored and have no business
# carrying a per-directory README; skipping them keeps the check honest
# whether or not vendoring has run.
_VENDORED_STATIC: frozenset[str] = frozenset({"katex", "shaka", "fonts", "lucide"})


def _skipped(parts: tuple[str, ...]) -> bool:
    if any(p.startswith("_") or p.startswith(".") for p in parts):
        return True
    return parts[:2] == ("web", "static") and len(parts) >= 3 and parts[2] in _VENDORED_STATIC


def main() -> int:
    failures: list[str] = []
    for root in ROOTS:
        if not root.exists():
            continue

        if not (root / "README.md").exists():
            failures.append(f"{root}: missing README.md")

        # Exclude all subdirectories under 'decks'
        if root.name == "decks":
            continue

        for sub in sorted(p for p in root.rglob("*") if p.is_dir()):
            rel_parts = sub.relative_to(root).parts
            if _skipped(rel_parts):
                continue
            readme = sub / "README.md"
            if not readme.exists():
                failures.append(f"{sub}: missing README.md")
                continue
            lines = readme.read_text(encoding="utf-8").splitlines()
            if len(lines) > LIMIT:
                failures.append(f"{sub}: README.md is {len(lines)} lines (>{LIMIT})")

    for f in failures:
        print(f, file=sys.stderr)

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
