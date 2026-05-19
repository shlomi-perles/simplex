"""Pre-commit hook: verify GitHub issue/PR link text matches link target.

Scans the markdown files passed in argv for patterns like ``[#123](URL)``
or ``[issue #123](URL)`` where the URL ends in ``/issues/N`` or ``/pull/N``
and asserts that the visible number matches the target number.

The hook exits non-zero (and prints offenders) when a mismatch is found so
maintainers don't merge stale cross-references after copy-pasting.

Usage (driven by pre-commit; not invoked directly): one or more markdown
file paths in ``sys.argv[1:]``.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# [<visible-text>](<url>)  -- non-greedy, no nested brackets allowed.
_LINK = re.compile(r"\[([^\]]+)\]\((https?://[^)\s]+)\)")
_VISIBLE_NUM = re.compile(r"#(\d+)")
_TARGET_NUM = re.compile(r"/(?:issues|pull)/(\d+)(?:[/#?]|$)")


def check_file(path: Path) -> list[str]:
    errors: list[str] = []
    text = path.read_text(encoding="utf-8")
    for line_no, line in enumerate(text.splitlines(), start=1):
        for match in _LINK.finditer(line):
            visible, url = match.group(1), match.group(2)
            vis = _VISIBLE_NUM.search(visible)
            tgt = _TARGET_NUM.search(url)
            if vis and tgt and vis.group(1) != tgt.group(1):
                errors.append(
                    f"{path}:{line_no}: "
                    f"link text says #{vis.group(1)} but URL points to #{tgt.group(1)}"
                )
    return errors


def main(argv: list[str]) -> int:
    failures: list[str] = []
    for arg in argv:
        path = Path(arg)
        if not path.is_file() or path.suffix.lower() != ".md":
            continue
        failures.extend(check_file(path))
    if failures:
        sys.stderr.write("\n".join(failures) + "\n")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
