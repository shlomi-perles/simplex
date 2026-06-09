"""Browser-level smoke tests for the generated deck player."""

from __future__ import annotations

import re
from collections.abc import Generator, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from fractions import Fraction
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from typing import cast

import av
import numpy as np
import pytest
from playwright.sync_api import Browser, BrowserContext, Error, Page, expect, sync_playwright

from simplex.manifest import SceneCue, SceneCueManifest
from simplex.section import CueKind
from simplex.web.builder import build
from simplex.web.range_server import RangeRequestHandlerMixin
from simplex.web.site_config import SiteConfig

pytestmark = pytest.mark.browser


class _QuietHTTPRequestHandler(RangeRequestHandlerMixin, SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        return


def _write_solid_mp4(path: Path, color: tuple[int, int, int], frames: int = 30) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    width, height = 160, 90
    array = np.zeros((height, width, 3), dtype=np.uint8)
    array[:, :] = color
    with av.open(str(path), mode="w") as container:
        stream = container.add_stream("h264", rate=15)
        stream.width = width
        stream.height = height
        stream.pix_fmt = "yuv420p"
        stream.codec_context.gop_size = 1
        stream.codec_context.max_b_frames = 0
        stream.options = {"preset": "ultrafast", "tune": "zerolatency"}
        time_base = Fraction(1, 15)
        for index in range(frames):
            frame = av.VideoFrame.from_ndarray(array, format="rgb24")
            frame.pts = index
            frame.time_base = time_base
            for packet in stream.encode(frame):
                container.mux(packet)
        for packet in stream.encode():
            container.mux(packet)


@dataclass(frozen=True, slots=True)
class _BrowserPage:
    page: Page
    errors: list[str]


@pytest.fixture
def browser_page() -> Iterator[_BrowserPage]:
    with sync_playwright() as playwright:
        browser: Browser | None = None
        context: BrowserContext | None = None
        try:
            try:
                browser = playwright.chromium.launch()
            except Error as exc:
                message = str(exc)
                if "Executable doesn't exist" in message or "playwright install" in message:
                    pytest.skip(
                        "Playwright Chromium is not installed; run "
                        "`uv run playwright install chromium`."
                    )
                raise
            context = browser.new_context(
                color_scheme="dark",
                reduced_motion="reduce",
                viewport={"width": 1280, "height": 900},
            )
            page = context.new_page()
            errors: list[str] = []
            page.on("pageerror", lambda exc: errors.append(str(exc)))
            page.on(
                "console",
                lambda msg: errors.append(msg.text) if msg.type == "error" else None,
            )
            yield _BrowserPage(page=page, errors=errors)
            assert errors == []
        finally:
            if context is not None:
                context.close()
            if browser is not None:
                browser.close()


@contextmanager
def _serve_directory(root: Path) -> Generator[str]:
    handler = cast(
        type[SimpleHTTPRequestHandler],
        partial(_QuietHTTPRequestHandler, directory=str(root)),
    )
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def _write_deck(decks_dir: Path) -> None:
    deck = decks_dir / "alpha"
    deck.mkdir(parents=True, exist_ok=True)
    (deck / "deck.toml").write_text(
        """
slug = "alpha"
title = "Alpha"
summary = "Browser-test deck."
scenes = ["Intro", "KeyIdea"]

[web]
show_slide_number = true
show_clock = true
show_stopwatch = true
""".strip()
        + "\n",
        encoding="utf-8",
    )
    (deck / "slides.py").write_text("# empty test scene module\n", encoding="utf-8")
    (deck / "notes.md").write_text(
        "# Notes\n\nJump straight to [slide:key-idea].\n",
        encoding="utf-8",
    )


def _build_site(tmp_path: Path) -> Path:
    decks_dir = tmp_path / "decks"
    decks_dir.mkdir()
    _write_deck(decks_dir)
    site_dir = tmp_path / "site"
    build(
        decks_dir=decks_dir,
        site_dir=site_dir,
        render=False,
        site_cfg=SiteConfig(brand="Simplex"),
    )
    return site_dir


def _build_site_with_real_timeline_video(tmp_path: Path) -> Path:
    decks_dir = tmp_path / "decks"
    decks_dir.mkdir()
    _write_deck(decks_dir)
    site_dir = tmp_path / "site"
    for variant, color in {
        "dark": (40, 80, 180),
        "light": (210, 230, 245),
    }.items():
        media_dir = site_dir / "decks" / "alpha" / "media" / variant
        _write_solid_mp4(media_dir / "lecture.mp4", color=color, frames=60)
    build(
        decks_dir=decks_dir,
        site_dir=site_dir,
        render=False,
        site_cfg=SiteConfig(brand="Simplex"),
    )
    return site_dir


def _write_scene_cue_manifest(
    site_dir: Path,
    *,
    variant: str,
    scene: str,
    cues: tuple[SceneCue, ...],
    frames: int,
) -> None:
    SceneCueManifest(
        scene=scene,
        unit=f"slides:{scene}",
        fps=15,
        duration=frames / 15,
        duration_frames=frames,
        cues=cues,
    ).write(
        site_dir.parent
        / ".simplex_cache"
        / "decks"
        / "alpha"
        / variant
        / "intermediate"
        / "simplex-cues"
        / f"{scene}.json"
    )


def _build_site_with_fragmented_main_slide(tmp_path: Path) -> Path:
    decks_dir = tmp_path / "decks"
    decks_dir.mkdir()
    _write_deck(decks_dir)
    site_dir = tmp_path / "site"
    intro_cues = (
        SceneCue(
            id="intro",
            kind=CueKind.SLIDE,
            title="Intro",
            unit="slides:Intro",
            start_frame=0,
            end_frame=45,
            start=0,
            end=3,
            auto_id=True,
        ),
    )
    key_idea_cues = (
        SceneCue(
            id="key-idea",
            kind=CueKind.SLIDE,
            title="Key Idea",
            unit="slides:KeyIdea",
            start_frame=0,
            end_frame=45,
            start=0,
            end=3,
            auto_id=True,
        ),
        SceneCue(
            id="key-idea-2",
            kind=CueKind.FRAGMENT,
            title="Key Idea",
            unit="slides:KeyIdea",
            start_frame=45,
            end_frame=90,
            start=3,
            end=6,
            auto_id=True,
        ),
    )
    for variant, color in {
        "dark": (40, 80, 180),
        "light": (210, 230, 245),
    }.items():
        _write_scene_cue_manifest(
            site_dir,
            variant=variant,
            scene="Intro",
            cues=intro_cues,
            frames=45,
        )
        _write_scene_cue_manifest(
            site_dir,
            variant=variant,
            scene="KeyIdea",
            cues=key_idea_cues,
            frames=90,
        )
        media_dir = site_dir / "decks" / "alpha" / "media" / variant
        _write_solid_mp4(media_dir / "lecture.mp4", color=color, frames=90)
    build(
        decks_dir=decks_dir,
        site_dir=site_dir,
        render=False,
        site_cfg=SiteConfig(brand="Simplex"),
    )
    return site_dir


def _open_deck(page: Page, base_url: str) -> None:
    page.goto(f"{base_url}/decks/alpha/")
    expect(page.locator("iframe.deck-iframe")).to_have_count(0)
    expect(page.locator("[data-player-stage]")).to_be_visible()
    expect(page.locator("[data-player-slide-number]")).to_have_text("1 / 2")


def test_deck_controls_update_direct_player_and_notes_refs(
    tmp_path: Path,
    browser_page: _BrowserPage,
) -> None:
    site_dir = _build_site(tmp_path)

    with _serve_directory(site_dir) as base_url:
        page = browser_page.page
        _open_deck(page, base_url)

        page.get_by_role("button", name="Next slide").click()
        expect(page.locator("[data-counter]")).to_have_text("2 / 2")
        expect(page.locator('[data-slide-target="2"]')).to_have_attribute(
            "aria-current",
            "true",
        )

        page.get_by_role("button", name="Previous slide").click()
        expect(page.locator("[data-counter]")).to_have_text("1 / 2")
        page.locator('.deck-notes .slide-ref[data-slide="2"]').click()
        expect(page.locator("[data-counter]")).to_have_text("2 / 2")

        page.locator("[data-settings-toggle]").click()
        page.locator('[data-setting="slide-number"]').uncheck()
        expect(page.locator("[data-player-slide-number]")).to_be_hidden()


def test_true_slide_theme_switch_uses_local_override_without_losing_slide(
    tmp_path: Path,
    browser_page: _BrowserPage,
) -> None:
    site_dir = _build_site(tmp_path)

    with _serve_directory(site_dir) as base_url:
        page = browser_page.page
        _open_deck(page, base_url)

        page.get_by_role("button", name="Next slide").click()
        expect(page.locator("[data-counter]")).to_have_text("2 / 2")

        page.locator("[data-settings-toggle]").click()
        page.locator('[data-setting="slide-theme"]').click()

        expect(page.locator("iframe.deck-iframe")).to_have_count(0)
        expect(page.locator("[data-counter]")).to_have_text("2 / 2")
        expect(page.locator(".deck-grid")).to_have_class(
            re.compile(r"\bis-true-slide-theme-light\b"),
        )
        expect(page.locator("[data-player-progress-bar]")).to_have_css(
            "background-color",
            "rgb(16, 88, 194)",
        )
        active_border = page.evaluate(
            """
            () => getComputedStyle(
              document.querySelector('.deck-slide-card[aria-current="true"] .deck-slide-thumb'),
              '::after'
            ).borderColor
            """
        )
        assert active_border == "rgb(16, 88, 194)"
        assert page.evaluate("localStorage.getItem('simplex-slide-theme:alpha')") is None

        page.get_by_role("button", name="Previous slide").click()
        expect(page.locator("[data-counter]")).to_have_text("1 / 2")
        expect(page.locator(".deck-grid")).to_have_class(
            re.compile(r"\bis-true-slide-theme-light\b"),
        )
        page.reload()
        expect(page.locator("[data-player-stage]")).to_be_visible()
        expect(page.locator(".deck-grid")).not_to_have_class(
            re.compile(r"\bis-true-slide-theme-light\b"),
        )
        page.locator("[data-theme-toggle]").click()
        expect(page.locator(".deck-grid")).to_have_class(
            re.compile(r"\bis-true-slide-theme-light\b"),
        )


def test_initial_light_theme_selects_light_sidebar_thumbnails(
    tmp_path: Path,
    browser_page: _BrowserPage,
) -> None:
    site_dir = _build_site(tmp_path)

    with _serve_directory(site_dir) as base_url:
        page = browser_page.page
        page.add_init_script("window.localStorage.setItem('simplex-theme', 'light');")
        _open_deck(page, base_url)

        first_thumb = page.locator('[data-slide-target="1"] .deck-slide-thumb img')
        expect(first_thumb).to_have_attribute("src", re.compile(r"posters/light/"))
        page.get_by_role("button", name="Next slide").click()

        page.locator("[data-theme-toggle]").click()
        page.locator("[data-theme-toggle]").click()

        expect(page.locator("[data-counter]")).to_have_text("2 / 2")
        expect(page.locator(".deck-grid")).to_have_class(
            re.compile(r"\bis-true-slide-theme-light\b"),
        )


def test_homepage_cards_follow_global_theme(
    tmp_path: Path,
    browser_page: _BrowserPage,
) -> None:
    site_dir = _build_site(tmp_path)

    with _serve_directory(site_dir) as base_url:
        page = browser_page.page
        page.add_init_script("window.localStorage.setItem('simplex-theme', 'light');")
        page.goto(base_url)

        first_thumb = page.locator(".carousel-card img").first
        expect(first_thumb).to_have_attribute("src", re.compile(r"decks/alpha/posters/light/"))

        page.locator("[data-theme-toggle]").click()
        expect(first_thumb).to_have_attribute("src", re.compile(r"decks/alpha/posters/dark/"))


def test_active_thumbnail_border_uses_slide_theme_not_global_theme(
    tmp_path: Path,
    browser_page: _BrowserPage,
) -> None:
    site_dir = _build_site(tmp_path)

    with _serve_directory(site_dir) as base_url:
        page = browser_page.page
        page.add_init_script("window.localStorage.setItem('simplex-theme', 'light');")
        _open_deck(page, base_url)

        page.locator("[data-settings-toggle]").click()
        page.locator('[data-setting="slide-theme"]').click()

        active_border = page.evaluate(
            """
            () => getComputedStyle(
              document.querySelector('.deck-slide-card[aria-current="true"] .deck-slide-thumb'),
              '::after'
            ).borderColor
            """
        )
        assert active_border == "rgb(244, 200, 74)"


def test_slides_pdf_href_follows_slide_theme(
    tmp_path: Path,
    browser_page: _BrowserPage,
) -> None:
    site_dir = _build_site(tmp_path)

    with _serve_directory(site_dir) as base_url:
        page = browser_page.page
        _open_deck(page, base_url)

        slides_pdf = page.locator("[data-slides-pdf-link]")
        expect(slides_pdf).to_have_attribute("href", re.compile(r"exports/Alpha-slides\.pdf"))

        page.locator("[data-settings-toggle]").click()
        page.locator('[data-setting="slide-theme"]').click()
        expect(slides_pdf).to_have_attribute("href", re.compile(r"exports/Alpha-slides\.pdf"))


def test_direct_player_has_tap_zones_and_progress_bar(
    tmp_path: Path,
    browser_page: _BrowserPage,
) -> None:
    site_dir = _build_site(tmp_path)

    with _serve_directory(site_dir) as base_url:
        page = browser_page.page
        _open_deck(page, base_url)

        expect(page.locator("[data-player-progress]")).to_be_visible()
        expect(page.locator("[data-player-progress]")).to_have_css("height", "4px")
        progress = page.locator("[data-player-progress-bar]")
        expect(progress).to_have_css("transform", "matrix(0, 0, 0, 1, 0, 0)")

        page.locator("[data-tap='next']").click(position={"x": 20, "y": 20})
        expect(page.locator("[data-counter]")).to_have_text("2 / 2")
        expect(progress).not_to_have_css("transform", "matrix(0, 0, 0, 1, 0, 0)")
        page.keyboard.press("ArrowLeft")
        expect(page.locator("[data-tap='next']")).to_have_css("outline-style", "none")

        page.locator("[data-tap='prev']").click(position={"x": 20, "y": 20})
        expect(page.locator("[data-counter]")).to_have_text("1 / 2")


def test_keyboard_navigation_does_not_add_extra_thumbnail_focus_ring(
    tmp_path: Path,
    browser_page: _BrowserPage,
) -> None:
    site_dir = _build_site(tmp_path)

    with _serve_directory(site_dir) as base_url:
        page = browser_page.page
        _open_deck(page, base_url)

        second_card = page.locator('[data-slide-target="2"]')
        second_card.click()
        expect(page.locator("[data-counter]")).to_have_text("2 / 2")
        page.keyboard.press("ArrowLeft")
        expect(second_card).to_have_css("outline-style", "none")


def test_cue_navigation_seeks_one_timeline_without_source_swap(
    tmp_path: Path,
    browser_page: _BrowserPage,
) -> None:
    site_dir = _build_site_with_real_timeline_video(tmp_path)

    with _serve_directory(site_dir) as base_url:
        page = browser_page.page
        _open_deck(page, base_url)

        result = page.evaluate(
            """
            async () => {
              const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
              const video = () => document.querySelector('.deck-player-video.is-active');
              const waitFor = async (predicate, timeout = 8000) => {
                const start = performance.now();
                while (performance.now() - start < timeout) {
                  if (predicate()) return true;
                  await sleep(25);
                }
                return false;
              };
              await waitFor(() => (
                video() &&
                video().readyState >= 2 &&
                (video().currentSrc || video().src) &&
                document.querySelector('[data-player-preview]').hidden
              ));
              const beforeSrc = video().currentSrc || video().src;
              document.querySelector('[data-control="next"]').click();
              await waitFor(() => (
                document.querySelector('[data-counter]').textContent.trim() === '2 / 2' &&
                video().currentTime >= 1.8
              ));
              const afterNextSrc = video().currentSrc || video().src;
              const afterNextTime = video().currentTime;
              document.querySelector('[data-slide-target="1"]').click();
              await waitFor(() => document.querySelector('[data-counter]').textContent.trim() === '1 / 2');
              const afterJumpSrc = video().currentSrc || video().src;
              return {
                beforeSrc,
                afterNextSrc,
                afterJumpSrc,
                afterNextTime,
                videoCount: document.querySelectorAll('.deck-player-video').length
              };
            }
            """
        )

        assert result["videoCount"] == 1
        assert result["beforeSrc"].endswith("/media/dark/lecture.mp4")
        assert result["afterNextSrc"] == result["beforeSrc"]
        assert result["afterJumpSrc"] == result["beforeSrc"]
        assert result["afterNextTime"] >= 1.8


def test_deck_autoplays_first_cue_on_entry(
    tmp_path: Path,
    browser_page: _BrowserPage,
) -> None:
    site_dir = _build_site_with_real_timeline_video(tmp_path)

    with _serve_directory(site_dir) as base_url:
        page = browser_page.page
        _open_deck(page, base_url)

        result = page.evaluate(
            """
            async () => {
              const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
              const waitFor = async (predicate, timeout = 8000) => {
                const start = performance.now();
                while (performance.now() - start < timeout) {
                  if (predicate()) return true;
                  await sleep(25);
                }
                return false;
              };
              const video = document.querySelector('.deck-player-video.is-active');
              await waitFor(() => (
                video &&
                video.readyState >= 2 &&
                (video.currentSrc || video.src) &&
                document.querySelector('[data-player-preview]').hidden
              ));
              const start = video.currentTime;
              const advanced = await waitFor(() => video.currentTime > start + 0.08);
              return {
                advanced,
                paused: video.paused,
                currentTime: video.currentTime,
                playState: document.querySelector('[data-control="toggle-play"]').dataset.state
              };
            }
            """
        )

        assert result["advanced"] is True
        assert result["paused"] is False
        assert result["currentTime"] > 0.08
        assert result["playState"] == "playing"


def test_presentation_mode_auto_advances_to_next_main_slide(
    tmp_path: Path,
    browser_page: _BrowserPage,
) -> None:
    site_dir = _build_site_with_real_timeline_video(tmp_path)

    with _serve_directory(site_dir) as base_url:
        page = browser_page.page
        _open_deck(page, base_url)

        result = page.evaluate(
            """
            async () => {
              const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
              const waitFor = async (predicate, timeout = 6000) => {
                const start = performance.now();
                while (performance.now() - start < timeout) {
                  if (predicate()) return true;
                  await sleep(25);
                }
                return false;
              };
              const video = document.querySelector('.deck-player-video.is-active');
              await waitFor(() => (
                video.readyState >= 2 &&
                (video.currentSrc || video.src) &&
                document.querySelector('[data-player-preview]').hidden
              ));
              const mode = document.querySelector('[data-setting="watch-mode"]');
              mode.checked = false;
              mode.dispatchEvent(new Event('change', { bubbles: true }));
              video.currentTime = 1.92;
              await waitFor(() => video.currentTime >= 1.8);
              await video.play().catch(() => {});
              await waitFor(() => (
                !video.paused &&
                video.currentTime >= 2 &&
                document.querySelector('[data-counter]').textContent.trim() === '2 / 2'
              ));
              return {
                counter: document.querySelector('[data-counter]').textContent.trim(),
                currentTime: video.currentTime,
                paused: video.paused
              };
            }
            """
        )

        assert result["paused"] is False
        assert result["counter"] == "2 / 2"
        assert result["currentTime"] >= 2.0


def test_presentation_mode_keeps_active_main_slide_during_boundary_jitter(
    tmp_path: Path,
    browser_page: _BrowserPage,
) -> None:
    site_dir = _build_site_with_real_timeline_video(tmp_path)

    with _serve_directory(site_dir) as base_url:
        page = browser_page.page
        _open_deck(page, base_url)

        result = page.evaluate(
            """
            async () => {
              const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
              const waitFor = async (predicate, timeout = 8000) => {
                const start = performance.now();
                while (performance.now() - start < timeout) {
                  if (predicate()) return true;
                  await sleep(25);
                }
                return false;
              };
              const video = document.querySelector('.deck-player-video.is-active');
              const manifest = JSON.parse(document.querySelector('[data-player-manifest]').textContent);
              const secondSlide = manifest.cues.find((cue) => cue.kind === 'slide' && cue.ordinal === 2);
              await waitFor(() => (
                video.readyState >= 2 &&
                (video.currentSrc || video.src) &&
                document.querySelector('[data-player-preview]').hidden
              ));
              document.querySelector('[data-control="next"]').click();
              await waitFor(() => document.querySelector('[data-counter]').textContent.trim() === '2 / 2');
              video.pause();
              video.currentTime = Math.max(0, secondSlide.start - 0.15);
              video.dispatchEvent(new Event('timeupdate'));
              await sleep(100);
              return {
                counter: document.querySelector('[data-counter]').textContent.trim(),
                activeTarget: document.querySelector('.deck-slide-card[aria-current="true"]').dataset.slideTarget,
                hash: window.location.hash
              };
            }
            """
        )

        assert result["counter"] == "2 / 2"
        assert result["activeTarget"] == "2"
        assert result["hash"] == "#key-idea"


def test_presentation_mode_pauses_at_subcue_after_current_main_slide(
    tmp_path: Path,
    browser_page: _BrowserPage,
) -> None:
    site_dir = _build_site_with_fragmented_main_slide(tmp_path)

    with _serve_directory(site_dir) as base_url:
        page = browser_page.page
        _open_deck(page, base_url)

        result = page.evaluate(
            """
            async () => {
              const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
              const waitFor = async (predicate, timeout = 8000) => {
                const start = performance.now();
                while (performance.now() - start < timeout) {
                  if (predicate()) return true;
                  await sleep(25);
                }
                return false;
              };
              const video = document.querySelector('.deck-player-video.is-active');
              const manifest = JSON.parse(document.querySelector('[data-player-manifest]').textContent);
              const secondSlide = manifest.cues.find((cue) => cue.id === 'key-idea');
              await waitFor(() => (
                video.readyState >= 2 &&
                (video.currentSrc || video.src) &&
                document.querySelector('[data-player-preview]').hidden
              ));
              document.querySelector('[data-control="next"]').click();
              await waitFor(() => (
                document.querySelector('[data-counter]').textContent.trim() === '2 / 2' &&
                video.currentTime >= secondSlide.start - 0.1
              ));
              video.currentTime = secondSlide.end - 0.12;
              await waitFor(() => video.currentTime >= secondSlide.end - 0.16);
              await video.play().catch(() => {});
              await waitFor(() => video.paused && video.currentTime >= secondSlide.end - 0.25);
              return {
                counter: document.querySelector('[data-counter]').textContent.trim(),
                activeTarget: document.querySelector('.deck-slide-card[aria-current="true"]').dataset.slideTarget,
                currentTime: video.currentTime,
                paused: video.paused,
                hash: window.location.hash
              };
            }
            """
        )

        assert result["counter"] == "2 / 2"
        assert result["activeTarget"] == "2"
        assert result["paused"] is True
        assert result["currentTime"] == pytest.approx(4.5, abs=0.25)
        assert result["hash"] == "#key-idea"


def test_watch_mode_continues_across_cues(
    tmp_path: Path,
    browser_page: _BrowserPage,
) -> None:
    site_dir = _build_site_with_real_timeline_video(tmp_path)

    with _serve_directory(site_dir) as base_url:
        page = browser_page.page
        _open_deck(page, base_url)

        result = page.evaluate(
            """
            async () => {
              const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
              const waitFor = async (predicate, timeout = 6000) => {
                const start = performance.now();
                while (performance.now() - start < timeout) {
                  if (predicate()) return true;
                  await sleep(25);
                }
                return false;
              };
              const video = document.querySelector('.deck-player-video.is-active');
              await waitFor(() => (
                video.readyState >= 2 &&
                (video.currentSrc || video.src) &&
                document.querySelector('[data-player-preview]').hidden
              ));
              const mode = document.querySelector('[data-setting="watch-mode"]');
              mode.checked = true;
              mode.dispatchEvent(new Event('change', { bubbles: true }));
              video.currentTime = 1.92;
              await waitFor(() => video.currentTime >= 1.8);
              await video.play().catch(() => {});
              await waitFor(() => document.querySelector('[data-counter]').textContent.trim() === '2 / 2');
              return {
                counter: document.querySelector('[data-counter]').textContent.trim(),
                currentTime: video.currentTime,
                paused: video.paused
              };
            }
            """
        )

        assert result["counter"] == "2 / 2"
        assert result["currentTime"] >= 1.99


def test_theme_switch_preserves_cue_progress_on_target_timeline(
    tmp_path: Path,
    browser_page: _BrowserPage,
) -> None:
    site_dir = _build_site_with_real_timeline_video(tmp_path)

    with _serve_directory(site_dir) as base_url:
        page = browser_page.page
        _open_deck(page, base_url)

        result = page.evaluate(
            """
            async () => {
              const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
              const waitFor = async (predicate, timeout = 8000) => {
                const start = performance.now();
                while (performance.now() - start < timeout) {
                  if (predicate()) return true;
                  await sleep(25);
                }
                return false;
              };
              const video = () => document.querySelector('.deck-player-video.is-active');
              await waitFor(() => (
                video() &&
                video().readyState >= 2 &&
                (video().currentSrc || video().src) &&
                document.querySelector('[data-player-preview]').hidden
              ));
              document.querySelector('[data-control="next"]').click();
              await waitFor(() => (
                document.querySelector('[data-counter]').textContent.trim() === '2 / 2' &&
                video().currentTime >= 1.8
              ));
              video().currentTime = 2.05;
              await waitFor(() => video().currentTime >= 2.03);
              const beforeSrc = video().currentSrc || video().src;
              const beforeTime = video().currentTime;
              const beforePaused = video().paused;
              document.querySelector('[data-settings-toggle]').click();
              document.querySelector('[data-setting="slide-theme"]').click();
              const landed = await waitFor(() => (
                (video().currentSrc || video().src).includes('/media/light/lecture.mp4') &&
                video().readyState >= 2 &&
                video().currentTime >= beforeTime - 0.05 &&
                !video().paused
              ), 3000);
              return {
                beforeSrc,
                beforeTime,
                beforePaused,
                landed,
                afterSrc: video().currentSrc || video().src,
                currentTime: video().currentTime,
                paused: video().paused,
                counter: document.querySelector('[data-counter]').textContent.trim(),
                theme: document.querySelector('[data-player-stage]').dataset.slideTheme,
                videoCount: document.querySelectorAll('.deck-player-video').length
              };
            }
            """
        )

        assert result["beforeSrc"].endswith("/media/dark/lecture.mp4")
        assert result["afterSrc"].endswith("/media/light/lecture.mp4")
        assert result["counter"] == "2 / 2"
        assert result["theme"] == "light"
        assert result["videoCount"] == 1
        assert result["beforePaused"] is False
        assert result["landed"] is True
        assert result["paused"] is False
        assert result["currentTime"] >= result["beforeTime"] - 0.05


def test_theme_switch_preserves_paused_frame_without_poster_flash(
    tmp_path: Path,
    browser_page: _BrowserPage,
) -> None:
    site_dir = _build_site_with_real_timeline_video(tmp_path)

    with _serve_directory(site_dir) as base_url:
        page = browser_page.page
        _open_deck(page, base_url)

        result = page.evaluate(
            """
            async () => {
              const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
              const waitFor = async (predicate, timeout = 8000) => {
                const start = performance.now();
                while (performance.now() - start < timeout) {
                  if (predicate()) return true;
                  await sleep(25);
                }
                return false;
              };
              const video = () => document.querySelector('.deck-player-video.is-active');
              await waitFor(() => (
                video() &&
                video().readyState >= 2 &&
                (video().currentSrc || video().src) &&
                document.querySelector('[data-player-preview]').hidden
              ));
              video().currentTime = 0.95;
              await waitFor(() => video().currentTime >= 0.9);
              video().pause();
              await waitFor(() => video().paused);
              const beforeTime = video().currentTime;
              document.querySelector('[data-settings-toggle]').click();
              document.querySelector('[data-setting="slide-theme"]').click();
              await waitFor(() => (video().currentSrc || video().src).includes('/media/light/lecture.mp4'));
              await waitFor(() => video().readyState >= 2);
              return {
                afterSrc: video().currentSrc || video().src,
                currentTime: video().currentTime,
                beforeTime,
                paused: video().paused,
                previewHidden: document.querySelector('[data-player-preview]').hidden,
                theme: document.querySelector('[data-player-stage]').dataset.slideTheme,
              };
            }
            """
        )

        assert result["afterSrc"].endswith("/media/light/lecture.mp4")
        assert result["theme"] == "light"
        assert result["paused"] is True
        assert result["previewHidden"] is True
        assert result["currentTime"] == pytest.approx(result["beforeTime"], abs=0.25)
