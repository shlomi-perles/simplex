"""Site-wide configuration: committed `site.toml` merged with env overrides.

`site.toml` (in git) carries brand/nav/section ordering.
Env (`SIMPLEX_GA_TAG`, `SIMPLEX_BASE_URL`, `SIMPLEX_BRAND`, `SIMPLEX_PREVIEW`)
carries deployment concerns and is never committed.
"""

import os
import tomllib
from pathlib import Path
from typing import Self

from pydantic import BaseModel, ConfigDict


class NavLink(BaseModel):
    model_config = ConfigDict(frozen=True)
    label: str
    href: str


class SiteConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    brand: str = "Simplex"
    tagline: str | None = None
    nav: tuple[NavLink, ...] = ()
    default_section_order: tuple[str, ...] = ()

    # Deployment-only fields (loaded from env, not committed).
    ga_tag: str = ""
    base_url: str = "/"
    preview: bool = False

    @property
    def ga_enabled(self) -> bool:
        return bool(self.ga_tag) and not self.preview

    def url(self, path: str) -> str:
        """Resolve a site-relative path against `base_url`."""
        base = self.base_url.rstrip("/")
        clean = path.lstrip("/")
        if not base:
            return f"/{clean}"
        return f"{base}/{clean}"

    @classmethod
    def load(cls, repo_root: Path | None = None) -> Self:
        repo_root = repo_root or Path.cwd()
        committed: dict[str, object] = {}
        toml_path = repo_root / "site.toml"
        if toml_path.exists():
            committed = dict(tomllib.loads(toml_path.read_text(encoding="utf-8")))
            nav_raw = committed.pop("nav", ()) or ()
            if isinstance(nav_raw, list):
                committed["nav"] = tuple(NavLink(**dict(item)) for item in nav_raw)
            dso = committed.get("default_section_order")
            if isinstance(dso, list):
                committed["default_section_order"] = tuple(dso)

        env_overrides: dict[str, object] = {}
        if (ga := os.environ.get("SIMPLEX_GA_TAG")) is not None:
            env_overrides["ga_tag"] = ga
        if (base := os.environ.get("SIMPLEX_BASE_URL")) is not None:
            env_overrides["base_url"] = base
        if (brand := os.environ.get("SIMPLEX_BRAND")) is not None:
            env_overrides["brand"] = brand
        if (preview := os.environ.get("SIMPLEX_PREVIEW")) is not None:
            env_overrides["preview"] = preview.lower() in {"1", "true", "yes", "on"}

        return cls(**(committed | env_overrides))
