"""Browser-level smoke tests for the generated deck player."""

from __future__ import annotations

import re
from collections.abc import Generator, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from typing import cast

import av
import numpy as np
import pytest
from playwright.sync_api import Browser, BrowserContext, Error, Page, expect, sync_playwright

from simplex.web.builder import build
from simplex.web.site_config import SiteConfig

pytestmark = pytest.mark.browser


class _QuietHTTPRequestHandler(SimpleHTTPRequestHandler):
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
        for _ in range(frames):
            frame = av.VideoFrame.from_ndarray(array, format="rgb24")
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


def _build_site_with_real_subslide_video(tmp_path: Path) -> Path:
    decks_dir = tmp_path / "decks"
    decks_dir.mkdir()
    _write_deck(decks_dir)
    site_dir = tmp_path / "site"
    for variant, color in {
        "dark": (40, 80, 180),
        "light": (210, 230, 245),
    }.items():
        media_dir = site_dir / "decks" / "alpha" / "themes" / variant / "media"
        slides_dir = site_dir / "decks" / "alpha" / "themes" / variant / "slides"
        slides_dir.mkdir(parents=True, exist_ok=True)
        _write_solid_mp4(media_dir / "intro.mp4", color=color)
        _write_solid_mp4(media_dir / "detail.mp4", color=color)
        (slides_dir / "Intro.json").write_text(
            '{"slides":[{"file":"media/intro.mp4"},{"file":"media/detail.mp4"}]}',
            encoding="utf-8",
        )
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
        expect(first_thumb).to_have_attribute("src", re.compile(r"themes/light/"))
        page.get_by_role("button", name="Next slide").click()

        page.locator("[data-theme-toggle]").click()
        page.locator("[data-theme-toggle]").click()

        expect(page.locator("[data-counter]")).to_have_text("2 / 2")
        expect(page.locator(".deck-grid")).to_have_class(
            re.compile(r"\bis-true-slide-theme-light\b"),
        )


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


def test_theme_toggle_at_subslide_end_keeps_end_frame(
    tmp_path: Path,
    browser_page: _BrowserPage,
) -> None:
    site_dir = _build_site_with_real_subslide_video(tmp_path)

    with _serve_directory(site_dir) as base_url:
        page = browser_page.page
        _open_deck(page, base_url)

        result = page.evaluate(
            """
            async () => {
              const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
              const active = () => document.querySelector('.deck-player-video.is-active');
              const waitFor = async (predicate, timeout = 8000) => {
                const start = performance.now();
                while (performance.now() - start < timeout) {
                  if (predicate()) return true;
                  await sleep(25);
                }
                return false;
              };
              document.querySelector('[data-control="next"]').click();
              await waitFor(() => active() && active().dataset.subIndex === '1' && active().readyState >= 2);
              const video = active();
              const duration = Number.isFinite(video.duration) && video.duration > 0 ? video.duration : 2;
              video.currentTime = Math.max(0, duration - 0.18);
              await video.play().catch(() => {});
              await waitFor(() => active() && active().dataset.subIndex === '1' && active().ended, 5000);
              const beforeTheme = active().dataset.theme;
              document.querySelector('[data-setting="slide-theme"]').click();
              await waitFor(() => (
                active() &&
                active().dataset.subIndex === '1' &&
                active().dataset.theme !== beforeTheme &&
                active().readyState >= 2
              ));
              await sleep(350);
              const after = active();
              const preview = document.querySelector('[data-player-preview]');
              return {
                subIndex: after ? after.dataset.subIndex : '1',
                activeCount: document.querySelectorAll('.deck-player-video.is-active').length,
                currentTime: after ? after.currentTime : null,
                duration: after ? after.duration : duration,
                previewHidden: preview.hidden,
                previewSrc: preview.getAttribute('src'),
                videoCount: document.querySelectorAll('.deck-player-video').length,
              };
            }
            """
        )

        assert result["subIndex"] == "1"
        assert result["videoCount"] == 1
        if result["activeCount"]:
            assert result["currentTime"] >= result["duration"] - 0.12
        else:
            assert result["previewHidden"] is False
            assert "themes/light/" in result["previewSrc"]
