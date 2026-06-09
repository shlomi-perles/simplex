"""Builder threading for Manim passthrough args."""

from pathlib import Path
from typing import Any

import pytest

from simplex.manifest import SceneCue
from simplex.render.timeline import RenderedUnit
from simplex.section import CueKind
from simplex.web import builder
from simplex.web.site_config import SiteConfig


def _write_deck(root: Path, slug: str = "demo") -> Path:
    deck_dir = root / slug
    deck_dir.mkdir(parents=True)
    (deck_dir / "deck.toml").write_text(
        f'slug = "{slug}"\ntitle = "Demo"\nentrypoints = ["slides.scenes:Foo"]\n',
        encoding="utf-8",
    )
    slides_pkg = deck_dir / "slides"
    slides_pkg.mkdir()
    (slides_pkg / "__init__.py").write_text("", encoding="utf-8")
    (slides_pkg / "scenes.py").write_text("class Foo: ...\n", encoding="utf-8")
    return deck_dir


def test_build_threads_manim_args_to_deck_builder(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    decks_dir = tmp_path / "decks"
    _write_deck(decks_dir)
    calls: list[dict[str, Any]] = []

    def fake_build_deck(*args: Any, **kwargs: Any) -> builder._DeckCardAssets:
        calls.append(kwargs)
        return builder._DeckCardAssets(
            thumbnail=None,
            theme_thumbnails={},
            preview_gif=None,
            theme_preview_gifs={},
        )

    def fake_copy_static(_site_dir: Path) -> None:
        return None

    def noop_builder_step(*args: Any, **kwargs: Any) -> None:
        return None

    monkeypatch.setattr(builder, "_copy_static", fake_copy_static)
    monkeypatch.setattr(builder, "_build_deck", fake_build_deck)
    monkeypatch.setattr(builder, "_build_section_page", noop_builder_step)
    monkeypatch.setattr(builder, "_build_index", noop_builder_step)

    builder.build(
        decks_dir,
        tmp_path / "site",
        site_cfg=SiteConfig(brand="Simplex"),
        manim_args=("--disable_caching", "--fps", "60"),
    )

    assert len(calls) == 1
    assert calls[0]["manim_args"] == ("--disable_caching", "--fps", "60")


def test_render_variant_passes_manim_args_to_runner(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    deck = builder.DeckConfig.load(_write_deck(tmp_path))
    calls: list[dict[str, Any]] = []

    def fake_render(
        deck_arg: Any,
        *,
        output_dir: Path,
        manim_args: tuple[str, ...] = (),
        scenes: tuple[str, ...] = (),
        write_last_frame: bool = False,
    ) -> None:
        calls.append(
            {
                "deck": deck_arg.slug,
                "output_dir": output_dir,
                "manim_args": manim_args,
                "scenes": scenes,
                "write_last_frame": write_last_frame,
            }
        )

    def fake_load_units(*args: Any, **kwargs: Any) -> tuple[Any, ...]:
        return ()

    monkeypatch.setattr(builder.runner, "render", fake_render)
    monkeypatch.setattr(builder.timeline, "load_units", fake_load_units)

    builder._render_variant(
        deck,
        variant="dark",
        site_dir=tmp_path / "site",
        render=True,
        manim_args=("--disable_caching",),
        scenes=("Foo",),
        write_last_frame=True,
    )

    assert calls == [
        {
            "deck": "demo",
            "output_dir": tmp_path / ".simplex_cache" / "decks" / "demo" / "dark" / "intermediate",
            "manim_args": ("--disable_caching",),
            "scenes": ("Foo",),
            "write_last_frame": True,
        }
    ]


def test_render_variant_skips_unchanged_cached_units(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    deck = builder.DeckConfig.load(_write_deck(tmp_path))
    site_dir = tmp_path / "site"
    media_dir = tmp_path / ".simplex_cache" / "decks" / "demo" / "dark" / "intermediate"
    video = media_dir / "videos" / "slides" / "480p15" / "Foo.mp4"
    video.parent.mkdir(parents=True)
    video.write_bytes(b"cached")
    cue = SceneCue(
        id="foo",
        kind=CueKind.SLIDE,
        title="Foo",
        unit="slides.scenes:Foo",
        start_frame=0,
        end_frame=60,
        start=0.0,
        end=1.0,
    )
    unit = RenderedUnit(
        scene="Foo",
        unit="slides.scenes:Foo",
        source_file=deck.path / "slides" / "scenes.py",
        video=video,
        fps=60,
        duration=1.0,
        duration_frames=60,
        cues=(cue,),
    )
    state = builder._scene_fingerprints(deck, variant="dark", manim_args=())
    builder._render_state_path(media_dir).parent.mkdir(parents=True, exist_ok=True)
    builder._render_state_path(media_dir).write_text(
        '{"Foo": "' + state["Foo"] + '"}',
        encoding="utf-8",
    )

    def fail_render(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("unchanged cached unit should not be rendered")

    def load_cached_units(*args: Any, **kwargs: Any) -> tuple[RenderedUnit, ...]:
        return (unit,)

    monkeypatch.setattr(builder.runner, "render", fail_render)
    monkeypatch.setattr(builder.timeline, "load_units", load_cached_units)

    _media_dir, units = builder._render_variant(
        deck,
        variant="dark",
        site_dir=site_dir,
        render=True,
        manim_args=(),
        scenes=(),
    )

    assert units == (unit,)
