"""Copy `_template/` into a new deck directory."""

import shutil
from pathlib import Path


def scaffold(slug: str, decks_dir: Path) -> Path:
    """Materialize `decks/<slug>/` from `decks/_template/`, substituting the slug."""
    template = decks_dir / "_template"
    if not template.exists():
        raise FileNotFoundError(f"_template not found at {template}")
    dest = decks_dir / slug
    if dest.exists():
        raise FileExistsError(f"deck already exists at {dest}")
    shutil.copytree(template, dest)
    toml_path = dest / "deck.toml"
    toml_path.write_text(
        toml_path.read_text(encoding="utf-8").replace("__SLUG__", slug),
        encoding="utf-8",
    )
    return dest
