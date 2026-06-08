"""Timeline-native manifest schema shared by render, hosting, and playback."""

from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from simplex.section import CueKind

ThemeStrategy = Literal["rendered", "css_filter_fallback"]
ProgressiveMode = Literal["pyav", "hybrid_fragmented", "faststart", "copy", "missing"]
PlayerEngine = Literal["shaka", "native"]


class DeckInfo(BaseModel):
    model_config = ConfigDict(frozen=True)

    slug: str
    title: str


class Cue(BaseModel):
    """One semantic stop in the canonical lecture timeline."""

    model_config = ConfigDict(frozen=True)

    id: str
    ordinal: int
    kind: CueKind
    title: str
    unit: str
    start_frame: int
    end_frame: int
    start: float
    end: float
    poster: str | None = None
    thumbnail: str | None = None
    notes_ref: str | None = None

    @field_validator("id")
    @classmethod
    def _id_required(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("cue id must be non-empty")
        return value

    @model_validator(mode="after")
    def _frames_and_seconds_are_ordered(self) -> Self:
        if self.ordinal < 1:
            raise ValueError("cue ordinal is one-based")
        if self.end_frame < self.start_frame:
            raise ValueError("cue end_frame must be >= start_frame")
        if self.end < self.start:
            raise ValueError("cue end must be >= start")
        return self

    @property
    def duration(self) -> float:
        return max(0.0, self.end - self.start)

    @property
    def duration_frames(self) -> int:
        return max(0, self.end_frame - self.start_frame)

    @property
    def is_loop(self) -> bool:
        return self.kind.is_loop

    @property
    def is_skip(self) -> bool:
        return self.kind.is_skip


class ThemeMedia(BaseModel):
    model_config = ConfigDict(frozen=True)

    hls: str | None = None
    mp4: str | None = None


class ThemeTimeline(BaseModel):
    """Media timeline for one rendered or fallback theme role."""

    model_config = ConfigDict(frozen=True)

    id: str
    label: str
    strategy: ThemeStrategy
    media: ThemeMedia
    duration: float = 0.0
    background: str | None = None
    source_theme: str | None = None
    css_filter: str | None = None

    @model_validator(mode="after")
    def _fallback_has_source(self) -> Self:
        if self.strategy == "css_filter_fallback" and not self.source_theme:
            raise ValueError("css_filter_fallback themes require source_theme")
        return self


class ManifestAssets(BaseModel):
    model_config = ConfigDict(frozen=True)

    base_url: str = "."


class ManifestExports(BaseModel):
    model_config = ConfigDict(frozen=True)

    pdf: str | None = None
    pptx: str | None = None
    notes_pdf: str | None = None


class ManifestCompat(BaseModel):
    model_config = ConfigDict(frozen=True)

    progressive_mode: ProgressiveMode = "missing"
    player: PlayerEngine = "shaka"
    hls: bool = False


class DeckManifest(BaseModel):
    """Schema v2 public manifest consumed by the Simplex web player."""

    model_config = ConfigDict(frozen=True)

    schema_version: int = Field(default=2)
    deck: DeckInfo
    generated_at: str
    fps: int
    duration: float
    cues: tuple[Cue, ...] = ()
    themes: tuple[ThemeTimeline, ...] = ()
    assets: ManifestAssets = Field(default_factory=ManifestAssets)
    exports: ManifestExports = Field(default_factory=ManifestExports)
    budget_warnings: tuple[str, ...] = ()
    compat: ManifestCompat = Field(default_factory=ManifestCompat)

    @field_validator("schema_version")
    @classmethod
    def _schema_v2(cls, value: int) -> int:
        if value != 2:
            raise ValueError("Simplex player requires manifest schema_version 2")
        return value

    @model_validator(mode="after")
    def _cue_ids_are_stable_and_ordered(self) -> Self:
        seen: set[str] = set()
        previous_end = -1
        for expected_ordinal, cue in enumerate(self.cues, start=1):
            if cue.ordinal != expected_ordinal:
                raise ValueError("cue ordinals must be contiguous and one-based")
            if cue.id in seen:
                raise ValueError(f"duplicate cue id: {cue.id!r}")
            if cue.start_frame < previous_end:
                raise ValueError("cues must be ordered by frame")
            seen.add(cue.id)
            previous_end = cue.end_frame
        return self

    @property
    def deck_slug(self) -> str:
        return self.deck.slug

    @property
    def slide_count(self) -> int:
        return len([cue for cue in self.cues if cue.kind.is_slide])

    @property
    def total_duration_s(self) -> float:
        return self.duration

    def find(self, cue_id: str) -> Cue | None:
        return next((cue for cue in self.cues if cue.id == cue_id), None)

    def at(self, index: int) -> Cue:
        return self.cues[index]

    def theme(self, theme_id: str) -> ThemeTimeline | None:
        return next((theme for theme in self.themes if theme.id == theme_id), None)

    def to_public_json(self) -> str:
        return self.model_dump_json(indent=2, exclude_none=True)

    @classmethod
    def empty(cls, slug: str, title: str | None = None, *, fps: int = 60) -> Self:
        return cls(
            deck=DeckInfo(slug=slug, title=title or slug),
            generated_at=dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat(),
            fps=fps,
            duration=0.0,
            cues=(),
            themes=(),
        )


class SceneCue(BaseModel):
    """Unit-local cue metadata written by ``SimplexScene`` during render."""

    model_config = ConfigDict(frozen=True)

    id: str
    kind: CueKind
    title: str
    unit: str
    start_frame: int
    end_frame: int
    start: float
    end: float
    notes: str | None = None
    auto_id: bool = False


class SceneCueManifest(BaseModel):
    """Intermediate cue JSON emitted beside one rendered scene unit."""

    model_config = ConfigDict(frozen=True)

    schema_version: int = 1
    scene: str
    unit: str
    fps: int
    duration: float
    duration_frames: int
    cues: tuple[SceneCue, ...]

    def write(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.model_dump_json(indent=2, exclude_none=True), encoding="utf-8")

    @classmethod
    def read(cls, path: Path) -> Self:
        return cls.model_validate_json(path.read_text(encoding="utf-8"))
