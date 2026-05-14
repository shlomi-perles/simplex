"""DeckConfig -- pydantic model loaded from each deck's deck.toml."""

import re
import tomllib
from pathlib import Path

from pydantic import BaseModel, ConfigDict, field_validator

_SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class DeckConfig(BaseModel):
    model_config = ConfigDict(frozen=True)
    slug: str
    title: str
    summary: str = ""
    tags: tuple[str, ...] = ()
    theme: str = "dastimator_dark"
    scenes: tuple[str, ...] = ()
    quality: str = "high_quality"
    voiceover: bool = False
    path: Path

    @field_validator("slug")
    @classmethod
    def _slug_format(cls, value: str) -> str:
        if not _SLUG.match(value):
            raise ValueError(f"slug must be kebab-case (a-z0-9 with single hyphens), got {value!r}")
        return value

    @classmethod
    def load(cls, deck_dir: Path) -> "DeckConfig":
        toml_path = deck_dir / "deck.toml"
        data = tomllib.loads(toml_path.read_text(encoding="utf-8"))
        return cls(**data, path=deck_dir)
