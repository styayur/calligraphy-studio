from __future__ import annotations

import hashlib
import io
import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont

from app.providers.base import DatasetProvider, RawGlyphRecord

GLYPH_SIZE = 768
FONT_SIZE = 640


class FontManifestProvider(DatasetProvider):
    """Turns licensed TTF/OTF files into normalized transparent PNG Glyphs."""

    name = "font-manifest"

    def __init__(
        self,
        manifest_path: str | Path,
        characters: set[str] | None = None,
        include_noncommercial: bool = True,
    ) -> None:
        self.manifest_path = Path(manifest_path).resolve()
        self.root = self.manifest_path.parent
        self.characters = characters
        self.include_noncommercial = include_noncommercial

    def _manifest(self) -> dict[str, Any]:
        payload = json.loads(self.manifest_path.read_text(encoding="utf-8-sig"))
        if isinstance(payload, list):
            return {"fonts": payload}
        if not isinstance(payload, dict):
            raise ValueError("Font manifest must be a JSON object or list")
        return payload

    @staticmethod
    def _font_checksum(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    @staticmethod
    def _png_for_character(font: ImageFont.FreeTypeFont, character: str) -> bytes:
        image = Image.new("RGBA", (GLYPH_SIZE, GLYPH_SIZE), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        draw.text(
            (GLYPH_SIZE / 2, GLYPH_SIZE / 2),
            character,
            font=font,
            fill=(23, 20, 17, 255),
            anchor="mm",
        )
        buffer = io.BytesIO()
        image.save(buffer, format="PNG", optimize=True)
        return buffer.getvalue()

    def iter_records(self) -> Iterator[RawGlyphRecord]:
        manifest = self._manifest()
        default_characters = set(manifest.get("characters") or [])
        source_index = 0

        for entry in manifest.get("fonts", []):
            enabled = bool(entry.get("enabled", True))
            if not enabled:
                continue

            rights = dict(entry.get("rights") or {})
            if rights.get("commercial_use") is False and not self.include_noncommercial:
                continue

            configured_path = Path(str(entry["path"]))
            font_path = (
                configured_path.resolve()
                if configured_path.is_absolute()
                else (self.root / configured_path).resolve()
            )
            if not font_path.is_file():
                raise FileNotFoundError(f"Font file does not exist: {font_path}")

            requested = set(entry.get("characters") or self.characters or default_characters)
            if not requested:
                raise ValueError(f"Font entry {entry.get('id')} has no requested characters")

            checksum = self._font_checksum(font_path)
            with TTFont(font_path, lazy=True) as font_file:
                cmap = font_file.getBestCmap() or {}
            render_font = ImageFont.truetype(str(font_path), FONT_SIZE)
            for character in sorted(requested):
                if ord(character) not in cmap:
                    continue
                png = self._png_for_character(render_font, character)
                source_index += 1
                yield RawGlyphRecord(
                    character=character,
                    dataset=entry.get("dataset") or "Open Font Glyph Library",
                    calligrapher=entry.get("designer") or entry.get("calligrapher"),
                    style=entry.get("style") or "楷书",
                    dynasty=entry.get("dynasty"),
                    work=entry.get("family") or font_path.stem,
                    asset_bytes=png,
                    original_filename=f"{entry.get('id', font_path.stem)}-{character}.png",
                    width=GLYPH_SIZE,
                    height=GLYPH_SIZE,
                    license=entry.get("license"),
                    license_url=entry.get("license_url"),
                    source_uri=entry.get("source_uri"),
                    rights=rights,
                    provenance_type="font",
                    metadata={
                        "font_id": entry.get("id"),
                        "font_family": entry.get("family"),
                        "font_file": font_path.name,
                        "font_sha256": checksum,
                        "license_family": entry.get("license"),
                        "raster_size": GLYPH_SIZE,
                    },
                    source_index=source_index,
                )
