from __future__ import annotations

import hashlib
import io
import json
import unicodedata
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont

from app.providers.base import DatasetProvider, RawGlyphRecord
from app.domain import codepoints, unicode_script, RightsRecord
from app.services.font_shaper import FontShaper
from app.orthography import japanese_variant

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
        vertical: bool = False,
        datasets: set[str] | None = None,
    ) -> None:
        self.manifest_path = Path(manifest_path).resolve()
        self.root = self.manifest_path.parent
        self.characters = characters
        self.include_noncommercial = include_noncommercial
        self.vertical = vertical
        self.datasets = datasets

    def _manifest(self) -> dict[str, Any]:
        if self.manifest_path.stat().st_size > 16 * 1024 * 1024:
            raise ValueError("Excessive font manifest size")
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
            if self.datasets is not None and entry.get("dataset") not in self.datasets:
                continue
            enabled = entry.get("enabled", True)
            if not isinstance(enabled, bool):
                raise ValueError("Font enabled must be a boolean")
            if not enabled:
                continue

            rights = RightsRecord.model_validate(entry.get("rights") or {}).model_dump()
            if not self.include_noncommercial and rights.get("commercial_use") is not True:
                continue

            configured_path = Path(str(entry["path"]))
            font_path = (
                configured_path.resolve()
                if configured_path.is_absolute()
                else (self.root / configured_path).resolve()
            )
            if not font_path.is_file():
                raise FileNotFoundError(f"Font file does not exist: {font_path}")
            if not configured_path.is_absolute() and not font_path.is_relative_to(self.root):
                raise ValueError("Relative font path escapes manifest root")

            requested = set(entry.get("characters") or self.characters or default_characters)
            if not requested:
                raise ValueError(f"Font entry {entry.get('id')} has no requested characters")

            checksum = self._font_checksum(font_path)
            if entry.get("sha256") and entry["sha256"] != checksum:
                raise ValueError(f"Font checksum mismatch: {entry.get('id')}")
            if font_path.suffix.lower() not in {".ttf", ".otf"} or font_path.stat().st_size > 40 * 1024 * 1024:
                raise ValueError("Unsupported or excessive font file")
            with TTFont(font_path, lazy=True) as font_file:
                cmap = font_file.getBestCmap() or {}
            render_font = ImageFont.truetype(str(font_path), FONT_SIZE)
            shaper = FontShaper(font_path) if entry.get("language") == "ja" else None
            for character in sorted(requested):
                if any(ord(c) not in cmap for c in unicodedata.normalize('NFC', character)):
                    continue
                script = unicode_script(character)
                shaped = shaper.render(character, locale=entry.get("locale"), script=script, vertical=self.vertical) if shaper else None
                if shaper and shaped is None:
                    continue
                png = shaped[0] if shaped else self._png_for_character(render_font, character)
                shaping = shaped[1] if shaped else {"engine": "pillow-legacy", "source_sequence": character, "locale_aware": False}
                variant_type = entry.get("variant_type", "regional")
                canonical = None
                if entry.get("language") == "ja":
                    variant_type, canonical = japanese_variant(character, variant_type)
                variant_id = f"{entry.get('id')}:{'vertical' if self.vertical else 'horizontal'}:{'-'.join(codepoints(character))}"
                source_index += 1
                yield RawGlyphRecord(
                    character=character,
                    dataset=entry.get("dataset") or "Open Font Glyph Library",
                    calligrapher=entry.get("designer") or entry.get("calligrapher"),
                    style=entry.get("style"),
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
                    identity={"text": character, "codepoints": codepoints(character), "language": entry.get("language"), "locale": entry.get("locale"), "script": script, "canonical": canonical},
                    variant={"id": variant_id, "type": variant_type,
                             "font_glyph_id": shaping.get("font_glyph_ids", [None])[0] if shaping.get("font_glyph_ids") else None,
                             "glyph_name": shaping.get("glyph_names", [None])[0] if shaping.get("glyph_names") else None},
                    culture={key: (script if key == "script" else entry.get(key)) for key in ["language", "locale", "script", "writing_tradition", "orthography", "period", "region", "source_collection"]},
                    metadata={
                        "font_id": entry.get("id"),
                        "font_family": entry.get("family"),
                        "font_version":entry.get('font_version'),
                        "source_role": entry.get("source_role"),
                        "original_sha256": entry.get("original_sha256"),
                        "subset_command": entry.get("subset_command"),
                        "upstream_commit":entry.get('upstream_commit'),
                        "font_file": font_path.name,
                        "font_sha256": checksum,
                        "license_family": entry.get("license"),
                        "raster_size": GLYPH_SIZE,
                        "shaping": shaping,
                        "designer": entry.get("designer"),
                        "attribution": entry.get("attribution"),
                        "source_checksum": checksum,
                        "dataset_version": entry.get("upstream_commit"),
                        "source_uri": entry.get("source_uri"),
                        "license_text": entry.get("bundle_license_text", entry.get("license_text")),
                    },
                    source_index=source_index,
                )
