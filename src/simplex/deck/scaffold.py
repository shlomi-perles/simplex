"""Materialise a new deck folder from `decks/_template/`.

`simplex new <section>/<slug>` creates `decks/<section>/<slug>/`.
`simplex new <slug>` creates `decks/<slug>/` (featured section).
"""

import shutil
from pathlib import Path

from simplex.deck.section import FEATURED_SLUG

_TOKENS = ("__SLUG__", "__SECTION__", "__TITLE__")


def _humanise(slug: str) -> str:
    return slug.replace("-", " ").replace("_", " ").title()


def split_target(target: str) -> tuple[str, str]:
    """Split a `simplex new` argument into (section, slug)."""
    target = target.strip().strip("/")
    if "/" in target:
        section, _, slug = target.partition("/")
        if not section or not slug or "/" in slug:
            raise ValueError(f"target must be 'section/slug' or 'slug', got {target!r}")
        return section, slug
    return FEATURED_SLUG, target


def _substitute_tokens(path: Path, slug: str, section: str) -> None:
    text = path.read_text(encoding="utf-8")
    replaced = (
        text.replace("__SLUG__", slug)
        .replace("__SECTION__", section)
        .replace("__TITLE__", _humanise(slug))
    )
    if replaced != text:
        path.write_text(replaced, encoding="utf-8")


def scaffold(target: str, decks_dir: Path) -> Path:
    """Copy `_template/` to `decks/[section/]<slug>/`, substituting tokens."""
    template = decks_dir / "_template"
    if not template.exists():
        raise FileNotFoundError(f"_template not found at {template}")

    section, slug = split_target(target)

    if section == FEATURED_SLUG:
        dest = decks_dir / slug
    else:
        section_dir = decks_dir / section
        section_dir.mkdir(parents=True, exist_ok=True)
        dest = section_dir / slug

    if dest.exists():
        raise FileExistsError(f"deck already exists at {dest}")

    shutil.copytree(template, dest)
    for token_file in dest.rglob("*"):
        if not token_file.is_file():
            continue
        if token_file.suffix.lower() in {".png", ".jpg", ".jpeg", ".pdf", ".mp4"}:
            continue
        try:
            _substitute_tokens(token_file, slug=slug, section=section)
        except UnicodeDecodeError:
            continue
    return dest
