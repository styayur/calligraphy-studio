from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path
from urllib.request import Request, urlopen

from app.providers.base import RawGlyphRecord
from app.utils.image_meta import AssetMetadata, inspect_asset_bytes, inspect_asset_file, sha256_bytes
from app.utils.paths import safe_filename, slugify

MAX_REMOTE_BYTES = 100 * 1024 * 1024


@dataclass(slots=True)
class StoredAsset:
    url: str
    asset_type: str
    width: int
    height: int
    bbox: list[float]
    checksum: str
    original_filename: str | None


class AssetStore:
    def __init__(self, root: str | Path, download_remote: bool = False) -> None:
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.download_remote = download_remote

    def _destination(
        self,
        dataset: str,
        character: str,
        metadata: AssetMetadata,
        original_filename: str | None,
    ) -> Path:
        filename = safe_filename(character, "glyph")
        if original_filename:
            stem = safe_filename(Path(original_filename).stem, filename)
            filename = f"{filename}-{stem[:32]}" if stem != filename else stem
        filename = f"{filename}-{metadata.checksum[:12]}{metadata.extension}"
        return self.root / slugify(dataset, "dataset") / metadata.checksum[:2] / filename

    def _write(self, destination: Path, data: bytes) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        if not destination.exists():
            destination.write_bytes(data)

    def persist(self, record: RawGlyphRecord) -> StoredAsset:
        if record.asset_bytes is not None:
            metadata = inspect_asset_bytes(record.asset_bytes, record.original_filename)
            destination = self._destination(
                record.dataset, record.character, metadata, record.original_filename
            )
            self._write(destination, record.asset_bytes)
            relative_url = destination.relative_to(self.root).as_posix()
            return self._result(f"/assets/{relative_url}", metadata, record)

        if record.asset_path is not None:
            source = record.asset_path.resolve()
            if not source.is_file():
                raise FileNotFoundError(f"Asset does not exist: {source}")
            metadata = inspect_asset_file(source)
            destination = self._destination(
                record.dataset, record.character, metadata, record.original_filename or source.name
            )
            destination.parent.mkdir(parents=True, exist_ok=True)
            if not destination.exists():
                shutil.copy2(source, destination)
            relative_url = destination.relative_to(self.root).as_posix()
            return self._result(f"/assets/{relative_url}", metadata, record)

        if record.asset_url:
            if self.download_remote:
                request = Request(record.asset_url, headers={"User-Agent": "CalligraphyStudio/0.1"})
                with urlopen(request, timeout=30) as response:  # noqa: S310
                    data = response.read(MAX_REMOTE_BYTES + 1)
                if len(data) > MAX_REMOTE_BYTES:
                    raise ValueError("Remote asset exceeds the 100 MB import limit")
                metadata = inspect_asset_bytes(data, record.original_filename)
                destination = self._destination(
                    record.dataset, record.character, metadata, record.original_filename
                )
                self._write(destination, data)
                relative_url = destination.relative_to(self.root).as_posix()
                return self._result(f"/assets/{relative_url}", metadata, record)

            if not record.width or not record.height:
                raise ValueError("Remote assets require width/height unless --download-remote is used")
            extension = Path(record.asset_url.split("?")[0]).suffix.lower() or ".png"
            metadata = AssetMetadata(
                asset_type="svg" if extension == ".svg" else "raster",
                width=record.width,
                height=record.height,
                bbox=record.bbox or [0.0, 0.0, float(record.width), float(record.height)],
                checksum=sha256_bytes(record.asset_url.encode("utf-8")),
                extension=extension,
            )
            return self._result(record.asset_url, metadata, record)

        raise ValueError("Glyph record contains no asset bytes, path, or URL")

    @staticmethod
    def _result(url: str, metadata: AssetMetadata, record: RawGlyphRecord) -> StoredAsset:
        return StoredAsset(
            url=url,
            asset_type=metadata.asset_type,
            width=metadata.width,
            height=metadata.height,
            bbox=record.bbox or metadata.bbox,
            checksum=metadata.checksum,
            original_filename=record.original_filename,
        )