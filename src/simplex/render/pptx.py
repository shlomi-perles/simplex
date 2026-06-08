"""Build a minimal PowerPoint export from cue poster frames."""

from __future__ import annotations

import html
import io
import zipfile
from pathlib import Path

from PIL import Image, ImageDraw

from simplex.deck.config import DeckConfig
from simplex.manifest import Cue, DeckManifest

EMU_W = 12192000
EMU_H = 6858000


def export(deck: DeckConfig, manifest: DeckManifest, *, output_dir: Path) -> Path:
    """Write ``exports/<slug>.pptx`` from cue posters."""
    export_dir = output_dir / "exports"
    export_dir.mkdir(parents=True, exist_ok=True)
    pptx_path = export_dir / f"{deck.slug}.pptx"
    slides = tuple(cue for cue in manifest.cues if not cue.kind.is_skip)
    if not slides:
        slides = manifest.cues
    with zipfile.ZipFile(pptx_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        _write_static_parts(zf, slides)
        for index, cue in enumerate(slides, start=1):
            _write_slide(zf, index, cue)
            image = output_dir / cue.poster if cue.poster else None
            zf.writestr(f"ppt/media/image{index}.jpg", _jpeg_payload(image, cue.title))
    return pptx_path


def _write_static_parts(zf: zipfile.ZipFile, slides: tuple[Cue, ...]) -> None:
    overrides = "\n".join(
        f'<Override PartName="/ppt/slides/slide{i}.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>'
        for i in range(1, len(slides) + 1)
    )
    image_overrides = "\n".join(
        f'<Override PartName="/ppt/media/image{i}.jpg" ContentType="image/jpeg"/>'
        for i in range(1, len(slides) + 1)
    )
    zf.writestr(
        "[Content_Types].xml",
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Default Extension="jpg" ContentType="image/jpeg"/>'
        '<Default Extension="jpeg" ContentType="image/jpeg"/>'
        '<Default Extension="png" ContentType="image/png"/>'
        '<Override PartName="/ppt/presentation.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>'
        f"{overrides}{image_overrides}</Types>",
    )
    zf.writestr(
        "_rels/.rels",
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
        'Target="ppt/presentation.xml"/></Relationships>',
    )
    slide_ids = "\n".join(
        f'<p:sldId id="{255 + i}" r:id="rId{i}"/>' for i in range(1, len(slides) + 1)
    )
    zf.writestr(
        "ppt/presentation.xml",
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<p:presentation xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
        'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">'
        f"<p:sldIdLst>{slide_ids}</p:sldIdLst>"
        f'<p:sldSz cx="{EMU_W}" cy="{EMU_H}" type="wide"/>'
        '<p:notesSz cx="6858000" cy="9144000"/></p:presentation>',
    )
    rels = "\n".join(
        f'<Relationship Id="rId{i}" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" '
        f'Target="slides/slide{i}.xml"/>'
        for i in range(1, len(slides) + 1)
    )
    zf.writestr(
        "ppt/_rels/presentation.xml.rels",
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        f"{rels}</Relationships>",
    )


def _write_slide(zf: zipfile.ZipFile, index: int, cue: Cue) -> None:
    title = html.escape(cue.title)
    zf.writestr(
        f"ppt/slides/slide{index}.xml",
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
        'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">'
        "<p:cSld><p:spTree>"
        '<p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>'
        '<p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/>'
        '<a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>'
        '<p:pic><p:nvPicPr><p:cNvPr id="2" name="poster"/>'
        "<p:cNvPicPr/><p:nvPr/></p:nvPicPr><p:blipFill>"
        '<a:blip r:embed="rId1"/><a:stretch><a:fillRect/></a:stretch>'
        '</p:blipFill><p:spPr><a:xfrm><a:off x="0" y="0"/>'
        f'<a:ext cx="{EMU_W}" cy="{EMU_H}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/>'
        "</a:prstGeom></p:spPr></p:pic>"
        '<p:sp><p:nvSpPr><p:cNvPr id="3" name="title"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr>'
        '<p:spPr><a:xfrm><a:off x="457200" y="457200"/><a:ext cx="7000000" cy="600000"/>'
        "</a:xfrm></p:spPr><p:txBody><a:bodyPr/><a:lstStyle/><a:p><a:r><a:t>"
        f"{title}</a:t></a:r></a:p></p:txBody></p:sp>"
        "</p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sld>",
    )
    zf.writestr(
        f"ppt/slides/_rels/slide{index}.xml.rels",
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        f'<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" '
        f'Target="../media/image{index}.jpg"/></Relationships>',
    )


def _jpeg_payload(path: Path | None, title: str) -> bytes:
    image: Image.Image
    if path is not None and path.exists() and path.suffix.lower() in {".jpg", ".jpeg", ".png"}:
        try:
            with Image.open(path) as opened:
                image = opened.convert("RGB")
        except OSError:
            image = _placeholder(title)
    else:
        image = _placeholder(title)
    out = io.BytesIO()
    image.save(out, "JPEG", quality=88)
    return out.getvalue()


def _placeholder(title: str) -> Image.Image:
    image = Image.new("RGB", (1280, 720), "#242424")
    draw = ImageDraw.Draw(image)
    draw.text((64, 64), title, fill="#f2f2f2")
    return image
