from __future__ import annotations

import html
import json
from collections.abc import Iterator
from pathlib import Path
from urllib.request import Request, urlopen

from app.providers.base import DatasetProvider, RawGlyphRecord

HANZI_DATASET = "Hanzi Writer Structural Data"
HANZI_LICENSE = "ARPHIC PUBLIC LICENSE"
HANZI_LICENSE_URL = "https://github.com/chanind/hanzi-writer-data/blob/master/ARPHICPL.TXT"
HANZI_SOURCE_URI = "https://github.com/chanind/hanzi-writer-data"
HANZI_RIGHTS = {
    "commercial_use": True,
    "derivatives_allowed": True,
    "redistribution_allowed": True,
    "research_use": True,
    "share_alike_required": True,
    "attribution_required": True,
}


class HanziWriterProvider(DatasetProvider):
    name = "hanzi-writer"

    def __init__(
        self,
        character: str,
        cache_dir: str | Path,
        fetch_remote: bool = True,
        version: str = "2.0.1",
    ) -> None:
        if len(character) != 1:
            raise ValueError("HanziWriterProvider accepts exactly one character")
        self.character = character
        self.cache_dir = Path(cache_dir).resolve()
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.fetch_remote = fetch_remote
        self.version = version

    def _load_data(self) -> dict:
        cache_file = self.cache_dir / f"{self.character}.json"
        if cache_file.is_file():
            return json.loads(cache_file.read_text(encoding="utf-8"))
        if not self.fetch_remote:
            raise FileNotFoundError(f"Missing cached Hanzi Writer data for {self.character}")

        from urllib.parse import quote

        url = f"https://cdn.jsdelivr.net/npm/hanzi-writer-data@{self.version}/{quote(self.character)}.json"
        request = Request(url, headers={"User-Agent": "CalligraphyStudio/0.2"})
        with urlopen(request, timeout=20) as response:  # noqa: S310
            payload = response.read()
        cache_file.write_bytes(payload)
        return json.loads(payload)

    def _svg(self, payload: dict) -> bytes:
        strokes = payload.get("strokes") or []
        if not strokes:
            raise ValueError(f"Hanzi Writer data has no strokes for {self.character}")
        paths = "".join(
            f'<path d="{html.escape(str(path), quote=True)}" />' for path in strokes
        )
        svg = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<svg xmlns="http://www.w3.org/2000/svg" width="1024" height="1024" '
            'viewBox="0 0 1024 1024">'
            f'<g fill="#171411">{paths}</g></svg>'
        )
        return svg.encode("utf-8")

    def iter_records(self) -> Iterator[RawGlyphRecord]:
        payload = self._load_data()
        yield RawGlyphRecord(
            character=self.character,
            dataset=HANZI_DATASET,
            style="楷书结构",
            work="Make Me A Hanzi / Arphic Kaiti",
            asset_bytes=self._svg(payload),
            original_filename=f"{self.character}-hanzi-writer.svg",
            license=HANZI_LICENSE,
            license_url=HANZI_LICENSE_URL,
            source_uri=HANZI_SOURCE_URI,
            rights=dict(HANZI_RIGHTS),
            provenance_type="fallback",
            metadata={
                "model_version": self.version,
                "stroke_count": len(payload.get("strokes") or []),
                "modified": "Converted stroke paths into an SVG glyph asset.",
            },
            source_index=1,
        )
