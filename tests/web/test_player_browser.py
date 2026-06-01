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

import pytest
from playwright.sync_api import Browser, BrowserContext, Error, Page, expect, sync_playwright

from simplex.web.builder import build
from simplex.web.site_config import SiteConfig

pytestmark = pytest.mark.browser


class _QuietHTTPRequestHandler(SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        return


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


def _open_deck(page: Page, base_url: str) -> None:
    page.goto(f"{base_url}/decks/alpha/")
    frame = page.frame_locator("iframe.deck-iframe")
    expect(frame.locator(".reveal")).to_have_class(re.compile(r"\bready\b"))
    expect(frame.locator("#simplex-slide-number")).to_have_text("1 / 2")


def test_deck_controls_bridge_to_iframe_and_notes_refs(
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
        expect(
            page.frame_locator("iframe.deck-iframe").locator("#simplex-slide-number")
        ).to_be_hidden()


def test_true_slide_theme_switch_reloads_iframe_without_losing_slide(
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

        expect(page.locator("iframe.deck-iframe")).to_have_attribute(
            "src",
            re.compile(r"themes/light/slides\.html\?v="),
        )
        expect(page.locator("[data-counter]")).to_have_text("2 / 2")
        expect(page.frame_locator("iframe.deck-iframe").locator("html")).to_have_attribute(
            "data-theme",
            "light",
        )
