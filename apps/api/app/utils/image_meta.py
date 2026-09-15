from __future__ import annotations

import hashlib
import io
import re
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO
from xml.etree import ElementTree

from PIL import Image, ImageOps

RASTER_EXTENSIONS = {
    "JPEG": ".jpg",
    "PNG": ".png",
    "WEBP": ".webp",
    "BMP": ".bmp",
    "TIFF": ".tiff",
}


@dataclass(slots=True)
class AssetMetadata:
    asset_type: str
    width: int
    height: int
    bbox: list[float]
    checksum: str
    extension: str


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _svg_number(value: str | None, fallback: float) -> float:
    if not value:
        return fallback
    match = re.match(r"\s*([0-9.]+)", value)
    return float(match.group(1)) if match else fallback


def _inspect_svg(data: bytes, checksum: str) -> AssetMetadata:
    try:
        root = ElementTree.fromstring(data)
    except ElementTree.ParseError as exc:
        raise ValueError(f"Invalid SVG: {exc}") from exc

    view_box = root.attrib.get("viewBox", "").replace(",", " ").split()
    if len(view_box) == 4:
        x, y, width, height = (float(item) for item in view_box)
        bbox = [x, y, width, height]
    else:
        width = _svg_number(root.attrib.get("width"), 0)
        height = _svg_number(root.attrib.get("height"), 0)
        bbox = [0, 0, width, height]

    if bbox[2] <= 0 or bbox[3] <= 0:
        raise ValueError("SVG must define positive width/height or a valid viewBox")

    return AssetMetadata(
        asset_type="svg",
        width=max(1, round(bbox[2])),
        height=max(1, round(bbox[3])),
        bbox=bbox,
        checksum=checksum,
        extension=".svg",
    )


def _content_bbox(image: Image.Image) -> list[float]:
    rgba = image.convert("RGBA")
    alpha = rgba.getchannel("A")
    if alpha.getextrema()[0] < 255:
        box = alpha.getbbox()
    else:
        grayscale = rgba.convert("L")
        ink = grayscale.point(lambda pixel: 255 if pixel < 245 else 0)
        box = ink.getbbox()

    if box is None:
        return [0.0, 0.0, float(image.width), float(image.height)]
    left, top, right, bottom = box
    return [float(left), float(top), float(right - left), float(bottom - top)]


def inspect_asset_bytes(data: bytes, filename: str | None = None) -> AssetMetadata:
    checksum = sha256_bytes(data)
    if data.lstrip().startswith(b"<svg") or (
        filename is not None and filename.lower().endswith(".svg")
    ):
        return _inspect_svg(data, checksum)

    try:
        with Image.open(io.BytesIO(data)) as opened:
            image = ImageOps.exif_transpose(opened)
            image.load()
            image_format = (opened.format or "").upper()
            extension = RASTER_EXTENSIONS.get(image_format)
            if extension is None:
                raise ValueError(f"Unsupported raster format: {image_format or 'unknown'}")
            return AssetMetadata(
                asset_type="raster",
                width=image.width,
                height=image.height,
                bbox=_content_bbox(image),
                checksum=checksum,
                extension=extension,
            )
    except Exception as exc:
        if isinstance(exc, ValueError):
            raise
        raise ValueError(f"Unable to inspect image: {exc}") from exc


def inspect_asset_file(path: Path) -> AssetMetadata:
    data = path.read_bytes()
    return inspect_asset_bytes(data, filename=path.name)


def inspect_asset_stream(stream: BinaryIO, filename: str | None = None) -> AssetMetadata:
    data = stream.read()
    return inspect_asset_bytes(data, filename=filename)