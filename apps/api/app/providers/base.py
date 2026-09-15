from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator


@dataclass(slots=True)
class RawGlyphRecord:
    character: str
    dataset: str
    calligrapher: str | None = None
    style: str | None = None
    dynasty: str | None = None
    work: str | None = None
    asset_path: Path | None = None
    asset_url: str | None = None
    asset_bytes: bytes | None = None
    original_filename: str | None = None
    width: int | None = None
    height: int | None = None
    bbox: list[float] | None = None
    license: str | None = None
    license_url: str | None = None
    source_uri: str | None = None
    rights: dict = field(default_factory=dict)
    provenance_type: str = "original"
    confidence: float | None = None
    metadata: dict = field(default_factory=dict)
    source_index: int | None = None


class DatasetProvider(ABC):
    """Stable boundary between source-specific storage and the Glyph Store."""

    name: str

    @abstractmethod
    def iter_records(self) -> Iterator[RawGlyphRecord]:
        raise NotImplementedError