"""Build slide PDF exports from cue poster frames."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

from simplex.deck.config import DeckConfig
from simplex.manifest import DeckManifest
from simplex.render.filenames import pdf_name


def export(deck: DeckConfig, manifest: DeckManifest, *, output_dir: Path) -> Path:
    """Write ``exports/<title>-slides.pdf`` from cue poster images."""
    export_dir = output_dir / "exports"
    export_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = export_dir / pdf_name(deck, "slides")
    images: list[Image.Image] = []
    for cue in manifest.cues:
        if not cue.poster:
            continue
        image = _load_image(output_dir / cue.poster)
        if image is not None:
            images.append(image)
    if not images:
        images = [_placeholder_page(deck.title)]
    first, *rest = images
    first.save(str(pdf_path), "PDF", save_all=True, append_images=rest, resolution=100.0)
    return pdf_path


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
