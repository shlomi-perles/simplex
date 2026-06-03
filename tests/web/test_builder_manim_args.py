"""Builder threading for Manim passthrough args."""

from pathlib import Path
from typing import Any

import pytest

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


def test_maybe_render_passes_manim_args_to_runner(
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

    def fake_export(*args: Any, **kwargs: Any) -> None:
        return None

    monkeypatch.setattr(builder.runner, "render", fake_render)
    monkeypatch.setattr(builder.pdf, "export", fake_export)

    builder._maybe_render(
        deck,
        tmp_path / "out",
        render=True,
        manim_args=("--disable_caching",),
        scenes=("Foo", "Ghost"),
        write_last_frame=True,
    )

    assert calls == [
        {
            "deck": "demo",
            "output_dir": tmp_path / "out",
            "manim_args": ("--disable_caching",),
            "scenes": ("Foo",),
            "write_last_frame": True,
        }
    ]
