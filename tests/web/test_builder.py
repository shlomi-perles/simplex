"""`build(render=False)` emits timeline manifests and static deck pages."""

import json
from pathlib import Path

import av
import numpy as np

from simplex.deck.config import SlideThemeConfig
from simplex.web.builder import build
from simplex.web.site_config import NavLink, SiteConfig


def _write_solid_mp4(path: Path, color: tuple[int, int, int], frames: int = 12) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    width, height = 160, 90
    array = np.zeros((height, width, 3), dtype=np.uint8)
    array[:, :] = color
    with av.open(str(path), mode="w") as container:
        stream = container.add_stream("h264", rate=15)
        stream.width = width
        stream.height = height
        stream.pix_fmt = "yuv420p"
        for _ in range(frames):
            frame = av.VideoFrame.from_ndarray(array, format="rgb24")
            for packet in stream.encode(frame):
                container.mux(packet)
        for packet in stream.encode():
            container.mux(packet)


def _write_deck(root: Path, slug: str, title: str, *, scenes: tuple[str, ...] = ()) -> None:
    d = root / slug
    d.mkdir(parents=True, exist_ok=True)
    scenes_line = ""
    if scenes:
        joined = ", ".join(f'"{s}"' for s in scenes)
        scenes_line = f"scenes = [{joined}]\n"
    (d / "deck.toml").write_text(
        f'slug = "{slug}"\ntitle = "{title}"\nsummary = "tagline"\n{scenes_line}',
        encoding="utf-8",
    )
    (d / "slides.py").write_text("# empty\n", encoding="utf-8")
    (d / "notes.md").write_text("# Notes\n\nMath: $a+b$. See [slide:s1].\n", encoding="utf-8")


def _write_section(root: Path, name: str, title: str, order: int) -> None:
    section = root / name
    section.mkdir(parents=True, exist_ok=True)
    (section / "_section.toml").write_text(
        f'title = "{title}"\norder = {order}\n',
        encoding="utf-8",
    )


def test_build_emits_timeline_manifest_and_deck_page(tmp_path: Path) -> None:
    decks_dir = tmp_path / "decks"
    decks_dir.mkdir()
    _write_deck(decks_dir, "alpha", "Alpha", scenes=("S1",))
    _write_deck(decks_dir, "bravo", "Bravo", scenes=("S1",))

    site_dir = tmp_path / "site"
    build(
        decks_dir=decks_dir, site_dir=site_dir, render=False, site_cfg=SiteConfig(brand="Simplex")
    )

    index_html = (site_dir / "index.html").read_text(encoding="utf-8")
    alpha_html = (site_dir / "decks" / "alpha" / "index.html").read_text(encoding="utf-8")
    manifest = json.loads((site_dir / "decks" / "alpha" / "simplex-manifest.json").read_text())

    assert "Alpha" in index_html
    assert "carousel" in index_html
    assert "simplex.css?v=" in index_html
    assert "viewer.js?v=" in index_html
    assert manifest["schema_version"] == 2
    assert manifest["cues"][0]["id"] == "s1"
    assert manifest["themes"][0]["media"] == {}
    assert manifest["themes"][0]["background"] == "#242424"
    assert "budget_warnings" in manifest
    assert "data-player-stage" in alpha_html
    assert 'data-slide-background-dark="#242424"' in alpha_html
    assert 'data-slide-background-light="#EEEAD8"' in alpha_html
    assert "--deck-slide-bg: #242424" in alpha_html
    assert "data-player-manifest" in alpha_html
    assert "data-player-preview" in alpha_html
    assert "img.hidden = false" not in alpha_html
    assert "shaka/shaka-player.compiled.js" in alpha_html
    assert "iframe" not in alpha_html
    assert not (site_dir / "decks" / "alpha" / "slides.html").exists()
    assert manifest["exports"] == {"pdf": "exports/Alpha-slides-dark.pdf"}
    assert (site_dir / "decks" / "alpha" / "exports" / "Alpha-slides-dark.pdf").exists()
    assert (site_dir / "decks" / "alpha" / "exports" / "Alpha-slides-light.pdf").exists()
    assert not (site_dir / "decks" / "alpha" / "exports" / "Alpha-slides.pdf").exists()
    assert 'data-pdf-dark="exports/Alpha-slides-dark.pdf"' in alpha_html
    assert 'data-pdf-light="exports/Alpha-slides-light.pdf"' in alpha_html
    assert 'class="slide-ref"' in alpha_html


def test_no_render_build_reuses_existing_timeline_media(tmp_path: Path) -> None:
    decks_dir = tmp_path / "decks"
    decks_dir.mkdir()
    _write_deck(decks_dir, "alpha", "Alpha", scenes=("Intro", "KeyIdea"))
    site_dir = tmp_path / "site"
    for variant, color in {"dark": (40, 80, 180), "light": (210, 230, 245)}.items():
        media = site_dir / "decks" / "alpha" / "media" / variant
        _write_solid_mp4(media / "lecture.mp4", color=color)
        hls = media / "hls"
        hls.mkdir(parents=True)
        (hls / "master.m3u8").write_text("#EXTM3U\n", encoding="utf-8")

    build(
        decks_dir=decks_dir, site_dir=site_dir, render=False, site_cfg=SiteConfig(brand="Simplex")
    )

    manifest = json.loads((site_dir / "decks" / "alpha" / "simplex-manifest.json").read_text())
    dark = next(theme for theme in manifest["themes"] if theme["id"] == "dark")
    light = next(theme for theme in manifest["themes"] if theme["id"] == "light")
    assert dark["media"]["hls"] == "media/dark/hls/master.m3u8"
    assert dark["media"]["mp4"] == "media/dark/lecture.mp4"
    assert dark["background"] == "#242424"
    assert light["background"] == "#EEEAD8"
    assert manifest["duration"] > 0
    assert manifest["cues"][1]["start_frame"] > 0
    assert list((site_dir / "decks" / "alpha" / "posters" / "dark").glob("*.jpg"))


def test_build_resolves_nav_links_against_base_url(tmp_path: Path) -> None:
    decks_dir = tmp_path / "decks"
    decks_dir.mkdir()
    _write_deck(decks_dir, "alpha", "Alpha", scenes=("S1",))

    site_dir = tmp_path / "site"
    build(
        decks_dir=decks_dir,
        site_dir=site_dir,
        render=False,
        site_cfg=SiteConfig(
            brand="Simplex",
            base_url="/course",
            nav=(NavLink(label="Decks", href="/"),),
        ),
    )

    index_html = (site_dir / "index.html").read_text(encoding="utf-8")
    assert 'href="/course/"' in index_html
    assert 'href="/course/decks/alpha/"' in index_html


def test_build_can_emit_filter_mode_from_site_config(tmp_path: Path) -> None:
    decks_dir = tmp_path / "decks"
    decks_dir.mkdir()
    _write_deck(decks_dir, "alpha", "Alpha", scenes=("S1",))

    site_dir = tmp_path / "site"
    build(
        decks_dir=decks_dir,
        site_dir=site_dir,
        render=False,
        site_cfg=SiteConfig(brand="Simplex", slide_themes=SlideThemeConfig(enabled=False)),
    )

    html = (site_dir / "decks" / "alpha" / "index.html").read_text(encoding="utf-8")
    manifest = json.loads((site_dir / "decks" / "alpha" / "simplex-manifest.json").read_text())
    assert 'data-slide-theme-mode="filter"' in html
    assert any(theme["strategy"] == "css_filter_fallback" for theme in manifest["themes"])


def test_build_emits_section_pages_and_orders(tmp_path: Path) -> None:
    decks_dir = tmp_path / "decks"
    decks_dir.mkdir()
    _write_section(decks_dir, "graphs", "Graphs", order=1)
    _write_deck(decks_dir / "graphs", "bfs", "BFS", scenes=("S1",))
    _write_deck(decks_dir, "intro", "Featured Intro", scenes=("S1",))

    site_dir = tmp_path / "site"
    build(
        decks_dir=decks_dir, site_dir=site_dir, render=False, site_cfg=SiteConfig(brand="Simplex")
    )

    assert "Graphs" in (site_dir / "index.html").read_text(encoding="utf-8")
    assert "BFS" in (site_dir / "sections" / "graphs" / "index.html").read_text(encoding="utf-8")
    assert "Featured Intro" in (site_dir / "sections" / "featured" / "index.html").read_text(
        encoding="utf-8"
    )
