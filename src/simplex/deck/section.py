"""SectionConfig -- metadata for one carousel/subject under `decks/<dir>/`."""

import tomllib
from pathlib import Path
from typing import Self

from pydantic import BaseModel, ConfigDict

FEATURED_SLUG = "featured"
FEATURED_TITLE = "Featured"
_SECTION_TOML = "_section.toml"


def _humanise(slug: str) -> str:
    return slug.replace("-", " ").replace("_", " ").title()


class SectionConfig(BaseModel):
    model_config = ConfigDict(frozen=True)
    slug: str
    title: str
    order: int = 1000
    blurb: str = ""
    icon: str | None = None

    @classmethod
    def load(cls, section_dir: Path) -> Self:
        """Load `_section.toml` for `section_dir`; fall back to dir-name defaults."""
        toml_path = section_dir / _SECTION_TOML
        data: dict[str, object] = {}
        if toml_path.exists():
            data = dict(tomllib.loads(toml_path.read_text(encoding="utf-8")))
        data.setdefault("slug", section_dir.name)
        data.setdefault("title", _humanise(section_dir.name))
        return cls(**data)  # type: ignore[arg-type]

    @classmethod
    def featured(cls) -> Self:
        """Synthetic section for decks placed directly under `decks/`."""
        return cls(slug=FEATURED_SLUG, title=FEATURED_TITLE, order=0)
