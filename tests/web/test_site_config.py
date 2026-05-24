"""SiteConfig: TOML merging, env overrides, GA gating, base_url resolution."""

from pathlib import Path

import pytest

from simplex.web.site_config import NavLink, SiteConfig


def test_load_missing_file_returns_defaults(tmp_path: Path) -> None:
    cfg = SiteConfig.load(repo_root=tmp_path)
    assert cfg.brand == "Simplex"
    assert cfg.nav == ()
    assert cfg.ga_enabled is False


def test_load_reads_committed_toml(tmp_path: Path) -> None:
    (tmp_path / "site.toml").write_text(
        'brand = "Foo"\n'
        'tagline = "Bar"\n'
        'nav = [{ label = "Home", href = "/" }, { label = "GH", href = "https://x" }]\n',
        encoding="utf-8",
    )
    cfg = SiteConfig.load(repo_root=tmp_path)
    assert cfg.brand == "Foo"
    assert cfg.tagline == "Bar"
    assert cfg.nav == (
        NavLink(label="Home", href="/"),
        NavLink(label="GH", href="https://x"),
    )


def test_env_overrides_take_precedence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    (tmp_path / "site.toml").write_text('brand = "FileBrand"\n', encoding="utf-8")
    monkeypatch.setenv("SIMPLEX_BRAND", "EnvBrand")
    monkeypatch.setenv("SIMPLEX_GA_TAG", "G-XYZ")
    monkeypatch.setenv("SIMPLEX_BASE_URL", "/sub/")
    cfg = SiteConfig.load(repo_root=tmp_path)
    assert cfg.brand == "EnvBrand"
    assert cfg.ga_tag == "G-XYZ"
    assert cfg.base_url == "/sub/"
    assert cfg.ga_enabled is True


def test_preview_disables_ga(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("SIMPLEX_GA_TAG", "G-XYZ")
    monkeypatch.setenv("SIMPLEX_PREVIEW", "1")
    cfg = SiteConfig.load(repo_root=tmp_path)
    assert cfg.ga_tag == "G-XYZ"
    assert cfg.ga_enabled is False


def test_url_resolves_against_base() -> None:
    cfg = SiteConfig(base_url="/")
    assert cfg.url("decks/foo/") == "/decks/foo/"
    cfg = SiteConfig(base_url="/sub")
    assert cfg.url("decks/foo/") == "/sub/decks/foo/"
    cfg = SiteConfig(base_url="/sub/")
    assert cfg.url("/decks/foo/") == "/sub/decks/foo/"


def test_nav_url_preserves_external_and_hash_links() -> None:
    cfg = SiteConfig(base_url="/lectures")
    assert cfg.nav_url("/") == "/lectures/"
    assert cfg.nav_url("decks/foo/") == "/lectures/decks/foo/"
    assert cfg.nav_url("https://example.com/repo") == "https://example.com/repo"
    assert cfg.nav_url("#main") == "#main"
