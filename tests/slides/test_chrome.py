"""make_chrome -- pure factory, returns mobjects + a fresh shrunk Region."""

import pytest

pytest.importorskip("manim")

from simplex.engine.region import Region
from simplex.slides.chrome import Chrome, make_chrome
from simplex.theme import presets


def test_chrome_with_header_only() -> None:
    region = Region.full_frame()
    chrome = make_chrome(presets.SIMPLEX_DARK, region, header="Title")
    assert isinstance(chrome, Chrome)
    assert "header" in chrome.mobjects
    assert "footer" not in chrome.mobjects


def test_chrome_does_not_mutate_input_region() -> None:
    region = Region.full_frame()
    original = (region.top, region.bottom, region.left, region.right)
    make_chrome(presets.SIMPLEX_DARK, region, header="Title", footer="Footer")
    assert (region.top, region.bottom, region.left, region.right) == original


def test_chrome_body_region_is_shrunk_below_header() -> None:
    region = Region.full_frame()
    chrome = make_chrome(presets.SIMPLEX_DARK, region, header="Title")
    expected_top = region.top - presets.SIMPLEX_DARK.spacing.header_height
    assert chrome.body_region.top == pytest.approx(expected_top)
    assert chrome.body_region.bottom == pytest.approx(region.bottom)


def test_chrome_body_region_is_shrunk_above_footer() -> None:
    region = Region.full_frame()
    chrome = make_chrome(presets.SIMPLEX_DARK, region, footer="cite")
    expected_bottom = region.bottom + presets.SIMPLEX_DARK.spacing.footer_height
    assert chrome.body_region.bottom == pytest.approx(expected_bottom)
    assert chrome.body_region.top == pytest.approx(region.top)


def test_chrome_empty_call_yields_no_mobjects_and_unchanged_region() -> None:
    region = Region.full_frame()
    chrome = make_chrome(presets.SIMPLEX_DARK, region)
    assert chrome.mobjects == {}
    assert chrome.body_region.top == pytest.approx(region.top)
    assert chrome.body_region.bottom == pytest.approx(region.bottom)


def test_chrome_unpacks_as_namedtuple() -> None:
    region = Region.full_frame()
    mobs, body = make_chrome(presets.SIMPLEX_DARK, region, header="t")
    assert "header" in mobs
    assert body.top < region.top
