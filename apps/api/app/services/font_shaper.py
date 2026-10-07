"""HarfBuzz shaping and FreeType glyph-ID rasterisation (portable wheels)."""
from __future__ import annotations

import hashlib
import io
from pathlib import Path

import freetype
import uharfbuzz as hb
from fontTools.ttLib import TTFont
from PIL import Image

SCRIPT_TAGS = {"Han": "Hani", "Hiragana": "Hira", "Katakana": "Kana"}


class FontShaper:
    def __init__(self, path: Path):
        if path.suffix.lower() not in {".ttf", ".otf"} or path.stat().st_size > 40 * 1024 * 1024:
            raise ValueError("Unsupported or excessive font file")
        self.data = path.read_bytes()
        self.checksum = hashlib.sha256(self.data).hexdigest()
        self.font = hb.Font(hb.Face(self.data))
        self.upem = self.font.face.upem
        if not 16 <= self.upem <= 16384:
            raise ValueError('Invalid font units per em')
        self.font.scale = (self.upem, self.upem)
        self.face = freetype.Face(str(path))
        with TTFont(path, lazy=True) as tt:
            self.names = tt.getGlyphOrder()

    def shape(self, text: str, *, locale: str | None = None, script: str | None = None,
              vertical: bool = False, features: dict | None = None):
        if not text or len(text) > 32:
            raise ValueError("Shape one bounded Unicode sequence")
        buffer = hb.Buffer()
        buffer.add_str(text)
        buffer.guess_segment_properties()
        if locale:
            buffer.language = locale
        if script:
            buffer.script = SCRIPT_TAGS.get(script, script)
        buffer.direction = "ttb" if vertical else "ltr"
        enabled = {"locl": 1, "vert": int(vertical), "vrt2": int(vertical), **(features or {})}
        hb.shape(self.font, buffer, enabled)
        if any(info.codepoint == 0 for info in buffer.glyph_infos):
            return None
        return buffer, {"engine": "harfbuzz-freetype", "harfbuzz_version": hb.version_string(),
                        "source_sequence": text, "font_glyph_ids": [i.codepoint for i in buffer.glyph_infos],
                        "glyph_names": [self.names[i.codepoint] for i in buffer.glyph_infos],
                        "features": enabled, "locale": locale, "script": script,
                        "direction": "ttb" if vertical else "ltr", "font_sha256": self.checksum}

    def render(self, text: str, *, size: int = 768, **options):
        result = self.shape(text, **options)
        if result is None:
            return None
        buffer, metadata = result
        pixels = round(size * 0.82)
        self.face.set_pixel_sizes(0, pixels)
        factor = pixels / self.upem
        tiles = []
        pen_x = pen_y = 0
        for info, position in zip(buffer.glyph_infos, buffer.glyph_positions):
            extents = self.font.get_glyph_extents(info.codepoint)
            if extents and (max(abs(extents.width),abs(extents.height))*factor > 16000 or abs(extents.width*extents.height)*factor**2 > 32_000_000):
                raise ValueError('Excessive glyph raster bounds')
            self.face.load_glyph(info.codepoint, freetype.FT_LOAD_RENDER | freetype.FT_LOAD_NO_HINTING)
            slot = self.face.glyph
            bitmap = slot.bitmap
            if bitmap.width and bitmap.rows:
                mask = Image.frombytes("L", (bitmap.width, bitmap.rows), bytes(bitmap.buffer), "raw", "L", abs(bitmap.pitch))
                x = round((pen_x + position.x_offset) * factor) + slot.bitmap_left
                y = -round((pen_y + position.y_offset) * factor) - slot.bitmap_top
                tiles.append((mask, x, y))
            pen_x += position.x_advance
            pen_y += position.y_advance
        if not tiles:
            return None
        left = min(x for mask, x, y in tiles)
        top = min(y for mask, x, y in tiles)
        right = max(x + mask.width for mask, x, y in tiles)
        bottom = max(y + mask.height for mask, x, y in tiles)
        if max(right-left,bottom-top) > 16000 or (right-left)*(bottom-top) > 32_000_000:
            raise ValueError('Excessive composed glyph bounds')
        ink = Image.new("L", (right-left, bottom-top))
        for mask, x, y in tiles:
            # Marks are composited rather than replacing overlapping ink.
            from PIL import ImageChops
            area = ink.crop((x-left, y-top, x-left+mask.width, y-top+mask.height))
            ink.paste(ImageChops.lighter(area, mask), (x-left, y-top))
        fit = min(1, size * 0.88 / ink.width, size * 0.88 / ink.height)
        if fit < 1:
            ink = ink.resize((max(1, round(ink.width*fit)), max(1, round(ink.height*fit))), Image.Resampling.LANCZOS)
        dx, dy = (size-ink.width)//2, (size-ink.height)//2
        if options.get("locale", "") == "ja-JP" and text in "、。":
            dx, dy = (round(size * 0.78)-ink.width//2, round(size * 0.22)-ink.height//2) if options.get("vertical") else (round(size*0.22)-ink.width//2, round(size*0.78)-ink.height//2)
        image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        layer = Image.new("RGBA", ink.size, (23, 27, 26, 255))
        image.paste(layer, (dx, dy), ink)
        output = io.BytesIO()
        image.save(output, format="PNG", optimize=True)
        return output.getvalue(), metadata
