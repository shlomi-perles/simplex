"""Build slide PDF exports from cue poster frames."""

from __future__ import annotations

import re
from collections.abc import Mapping
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageOps

from simplex.deck.config import DeckConfig
from simplex.manifest import DeckManifest
from simplex.render.filenames import pdf_name

_FILTER_STEP = re.compile(r"([a-z-]+)\(([^)]*)\)")


def export(
    deck: DeckConfig,
    manifest: DeckManifest,
    *,
    output_dir: Path,
    variant: str | None = None,
    posters: Mapping[str, str | Path] | None = None,
    css_filter: str | None = None,
) -> Path:
    """Write a slide PDF from cue poster images."""
    export_dir = output_dir / "exports"
    export_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = export_dir / pdf_name(deck, "slides" if variant is None else f"slides-{variant}")
    poster_paths = (
        posters
        if posters is not None
        else {cue.id: cue.poster for cue in manifest.cues if cue.poster is not None}
    )
    images: list[Image.Image] = []
    for cue in manifest.cues:
        poster = poster_paths.get(cue.id)
        if poster is None:
            continue
        image = _load_image(_resolve_poster(output_dir, poster))
        if image is not None:
            image = _apply_css_filter(image, css_filter)
            images.append(image)
    if not images:
        images = [_apply_css_filter(_placeholder_page(deck.title), css_filter)]
    first, *rest = images
    first.save(str(pdf_path), "PDF", save_all=True, append_images=rest, resolution=100.0)
    return pdf_path


def _resolve_poster(output_dir: Path, path: str | Path) -> Path:
    poster = Path(path)
    return poster if poster.is_absolute() else output_dir / poster


def _load_image(path: Path) -> Image.Image | None:
    if not path.exists() or path.suffix.lower() not in {".jpg", ".jpeg", ".png"}:
        return None
    try:
        with Image.open(path) as image:
            return image.convert("RGB")
    except OSError:
        return None


def _placeholder_page(title: str) -> Image.Image:
    image = Image.new("RGB", (1280, 720), "#242424")
    draw = ImageDraw.Draw(image)
    draw.text((64, 64), title, fill="#f2f2f2")
    return image


def _apply_css_filter(image: Image.Image, css_filter: str | None) -> Image.Image:
    if not css_filter:
        return image
    filtered = image
    for name, raw_value in _FILTER_STEP.findall(css_filter):
        if name == "invert":
            amount = _css_number(raw_value, default=1.0)
            inverted = ImageOps.invert(filtered)
            filtered = Image.blend(filtered, inverted, max(0.0, min(1.0, amount)))
        elif name == "hue-rotate":
            filtered = _hue_rotate(filtered, _css_degrees(raw_value))
        elif name == "saturate":
            filtered = ImageEnhance.Color(filtered).enhance(_css_number(raw_value))
        elif name == "contrast":
            filtered = ImageEnhance.Contrast(filtered).enhance(_css_number(raw_value))
        elif name == "brightness":
            filtered = ImageEnhance.Brightness(filtered).enhance(_css_number(raw_value))
    return filtered


def _css_number(raw: str, *, default: float = 1.0) -> float:
    value = raw.strip()
    if not value:
        return default
    try:
        if value.endswith("%"):
            return float(value[:-1]) / 100
        return float(value)
    except ValueError:
        return default


def _css_degrees(raw: str) -> float:
    value = raw.strip()
    try:
        if value.endswith("turn"):
            return float(value[:-4]) * 360
        if value.endswith("rad"):
            return float(value[:-3]) * 180 / 3.141592653589793
        if value.endswith("deg"):
            return float(value[:-3])
        return float(value)
    except ValueError:
        return 0.0


def _hue_rotate(image: Image.Image, degrees: float) -> Image.Image:
    hue, saturation, value = image.convert("HSV").split()
    shift = round(degrees / 360 * 255)
    lookup = [(pixel + shift) % 256 for pixel in range(256)]
    shifted = hue.point(lookup)
    return Image.merge("HSV", (shifted, saturation, value)).convert("RGB")
