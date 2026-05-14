"""DeckConfig -- pydantic model loaded from each deck's deck.toml.

Two scene-list spellings are accepted:

- `entrypoints = ["slides.intro:Title", ...]` -- preferred, points at scene
  classes inside the deck's `slides/` package.
- `scenes = ["Title", ...]` -- legacy, bare class names in a top-level
  `slides.py`. Kept for backwards compatibility with the single-file layout.

`section_slug` is populated by the registry, not the author.
"""

import re
import tomllib
from pathlib import Path
from typing import Self

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

_SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_ENTRYPOINT = re.compile(r"^[A-Za-z_][\w.]*:[A-Za-z_]\w*$")


class DeckConfig(BaseModel):
    model_config = ConfigDict(frozen=True)
    slug: str
    title: str
    summary: str = ""
    tags: tuple[str, ...] = ()
    theme: str = "dastimator_dark"
    scenes: tuple[str, ...] = ()
    entrypoints: tuple[str, ...] = ()
    quality: str = "high_quality"
    voiceover: bool = False
    category: str | None = None
    duration_minutes: int | None = None
    order: int = 1000
    path: Path
    section_slug: str = "featured"

    @field_validator("slug")
    @classmethod
    def _slug_format(cls, value: str) -> str:
        if not _SLUG.match(value):
            raise ValueError(f"slug must be kebab-case (a-z0-9 with single hyphens), got {value!r}")
        return value

    @field_validator("entrypoints")
    @classmethod
    def _entrypoint_format(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        for ep in value:
            if not _ENTRYPOINT.match(ep):
                raise ValueError(f"entrypoint must be 'module[.sub]:ClassName', got {ep!r}")
        return value

    @model_validator(mode="after")
    def _at_least_one_scene_source(self) -> Self:
        if not self.scenes and not self.entrypoints:
            # Allow empty for the template / unit tests, but flag a deck that
            # explicitly sets neither so misconfigured decks fail loudly.
            return self
        return self

    @property
    def scene_specs(self) -> tuple[str, ...]:
        """Return entrypoints if present, else legacy `slides.py`-relative scenes."""
        if self.entrypoints:
            return self.entrypoints
        return tuple(f"slides:{name}" for name in self.scenes)

    @property
    def scene_class_names(self) -> tuple[str, ...]:
        """Bare class names extracted from `scene_specs`."""
        return tuple(spec.rsplit(":", 1)[-1] for spec in self.scene_specs)

    def resolve_entrypoints(self) -> tuple[tuple[Path, tuple[str, ...]], ...]:
        """Group entrypoints by their source file, in declaration order.

        Each `module:Class` spec is resolved to the file that physically defines
        the class -- `slides/scenes.py` for `slides.scenes:Foo`, `slides.py` for
        the legacy single-file layout. Manim's `scene_classes_from_file` filters
        scene classes by `__module__.startswith(loaded_module_name)`, so a
        re-exporting `__init__.py` would drop them all; loading each defining
        file directly is the only layout that survives that check.
        """
        groups: dict[Path, list[str]] = {}
        for spec in self.scene_specs:
            module, _, class_name = spec.partition(":")
            file_path = self._module_to_file(module)
            groups.setdefault(file_path, []).append(class_name)
        return tuple((file_path, tuple(names)) for file_path, names in groups.items())

    def _module_to_file(self, module: str) -> Path:
        """Map `slides.foo.bar` to the deck-relative `.py` file that defines it."""
        parts = module.split(".")
        module_path = self.path.joinpath(*parts)
        as_file = module_path.with_suffix(".py")
        if as_file.exists():
            return as_file
        as_pkg = module_path / "__init__.py"
        if as_pkg.exists():
            return as_pkg
        raise FileNotFoundError(
            f"deck {self.slug!r}: entrypoint module {module!r} resolves to neither "
            f"{as_file} nor {as_pkg}"
        )

    @classmethod
    def load(cls, deck_dir: Path, *, section_slug: str = "featured") -> Self:
        toml_path = deck_dir / "deck.toml"
        data = tomllib.loads(toml_path.read_text(encoding="utf-8"))
        return cls(**data, path=deck_dir, section_slug=section_slug)
