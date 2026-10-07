"""Authoritative CODH v2 crops with upstream transcription preserved.

Archives are read in place, never extracted. Iterate coordinate CSVs row by row,
yield one crop at a time; importer checkpoints make retries checksum-idempotent.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import stat
import zipfile
from pathlib import Path, PurePosixPath
from typing import Callable
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, model_validator
from PIL import Image
from app.domain import CharacterIdentity, ScriptMetadata, codepoints, unicode_script, require_rights
from app.providers.base import RawGlyphRecord
from app.providers.japanese_historical import JapaneseHistoricalProvider
from app.utils.image_meta import inspect_asset_bytes, sha256_file

CODH_LICENSE = "CC-BY-SA-4.0"
CODH_URL = "https://codh.rois.ac.jp/char-shape/"
CODH_RIGHTS = dict(commercial_use=True, derivatives_allowed=True, redistribution_allowed=True,
                   research_use=True, attribution_required=True, font_license=False, share_alike_required=True)
CODH_ATTRIBUTION = "日本古典籍くずし字データセット (国文研所蔵／CODH加工), doi:10.20676/00000340"


def safe_local(root: Path, relative: str) -> Path:
    if not relative or "\\" in relative or ":" in relative or any(ord(c) < 32 for c in relative):
        raise ValueError("Unsafe local path")
    path = PurePosixPath(relative)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError("Path traversal")
    result = (root / relative).resolve()
    if not result.is_relative_to(root.resolve()):
        raise ValueError("Path escapes source root")
    return result


def validate_archive(archive: zipfile.ZipFile):
    total = 0
    names=set()
    for item in archive.infolist():
        safe_local(Path.cwd(), item.orig_filename)
        key=PurePosixPath(item.orig_filename).as_posix().casefold()
        if key in names:
            raise ValueError('Duplicate or case-colliding archive path')
        names.add(key)
        mode = item.external_attr >> 16
        if stat.S_ISLNK(mode) or item.flag_bits & 1:
            raise ValueError("Symlink or encrypted archive entry")
        if not item.is_dir() and Path(item.filename).suffix.lower() not in {".csv", ".jpg", ".jpeg", ".png", ".txt"}:
            raise ValueError("Unexpected archive file type")
        if item.file_size > 40 * 1024 * 1024 or item.file_size > max(item.compress_size, 1) * 500:
            raise ValueError("Excessive archive member")
        total += item.file_size
        if total > 30 * 1024**3:
            raise ValueError("Archive expansion exceeds 30 GB")


class CODHManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: int = Field(ge=2, le=2)
    dataset_version: str = "v2"
    assets: list[dict] = Field(default_factory=list)
    archives: list[dict] = Field(default_factory=list)
    provenance: dict = Field(default_factory=dict)

    @model_validator(mode='after')
    def validate_receipts(self):
        if len(self.archives)>1000 or len(self.assets)>50000:
            raise ValueError('Excessive receipt count; split manifests')
        for receipt in [*self.archives,*self.assets]:
            if not isinstance(receipt.get('file'),str) or len(receipt['file'])>2048:
                raise ValueError('Invalid receipt file')
            safe_local(Path.cwd(),receipt['file'])
            if not isinstance(receipt.get('sha256'),str) or not re.fullmatch(r'[0-9a-f]{64}',receipt['sha256']):
                raise ValueError('Invalid receipt checksum')
        for asset in self.assets:
            if Path(asset['file']).suffix.lower() not in {'.jpg','.jpeg','.png'}:
                raise ValueError('Unsupported historical crop type')
            if not isinstance(asset.get('variant_id'),str) or not 1<=len(asset['variant_id'])<=512:
                raise ValueError('Invalid historical occurrence ID')
            CharacterIdentity.model_validate(asset.get('identity') or {'text':asset.get('character')})
            ScriptMetadata.model_validate(asset.get('culture') or {})
        for receipt in self.archives:
            if Path(receipt['file']).suffix.lower()!='.zip' or not isinstance(receipt.get('books',{}),dict):
                raise ValueError('Invalid archive receipt')
            for key,book in receipt.get('books',{}).items():
                if not re.fullmatch(r'[A-Za-z0-9_-]{1,64}',key) or not isinstance(book,dict):
                    raise ValueError('Invalid book receipt')
                ScriptMetadata.model_validate(book.get('culture') or {})
        return self


class CODHKuzushijiProvider(JapaneseHistoricalProvider):
    name = "codh-kuzushiji"

    def __init__(self, manifest_path: str | Path, *, cancelled: Callable[[], bool] | None = None,
                 characters: set[str] | None = None, limit: int | None = None):
        self.path = Path(manifest_path).resolve()
        if self.path.stat().st_size > 16 * 1024 * 1024:
            raise ValueError("Excessive manifest size; use separate archives")
        self.manifest = CODHManifest.model_validate_json(self.path.read_bytes())
        if self.manifest.dataset_version != "v2":
            raise ValueError("Only the reviewed CODH v2 dataset is supported")
        self.cancelled, self.characters, self.limit = cancelled, characters, limit

    def _record(self, item: dict, data: bytes, source_checksum: str):
        with Image.open(io.BytesIO(data)) as image:
            if image.format not in {'JPEG','PNG'}:
                raise ValueError('CODH display assets must be JPEG or PNG')
        identity = CharacterIdentity.model_validate(item.get("identity") or {"text": item["character"]})
        culture = ScriptMetadata.model_validate(item.get("culture") or {})
        metadata = inspect_asset_bytes(data, item["file"])
        if metadata.asset_type != "raster":
            raise ValueError("CODH requires raster source crops")
        uri = item.get("source_uri", CODH_URL)
        parsed = urlparse(uri)
        if parsed.scheme != "https" or parsed.hostname != "codh.rois.ac.jp":
            raise ValueError("CODH source URI must be authoritative")
        rights = dict(CODH_RIGHTS)
        if item.get("rights") and any(item['rights'].get(key) != value for key, value in CODH_RIGHTS.items()):
            raise ValueError("CODH rights must retain the reviewed CC-BY-SA-4.0 obligations")
        require_rights(rights, bundle=True)
        return RawGlyphRecord(character=identity.text, dataset="CODH Kuzushiji", work=item.get("work"),
                              calligrapher=item.get("calligrapher"), style=None,
                              asset_bytes=data, original_filename=Path(item["file"]).name,
                              license=CODH_LICENSE, license_url="https://creativecommons.org/licenses/by-sa/4.0/",
                              source_uri=uri, rights=rights, provenance_type="original",
                              identity=identity.model_dump(), culture=culture.model_dump(),
                              variant={"type": "historical", "id": item["variant_id"]},
                              metadata={"page": item.get("page"), "source_bbox": item.get("bbox"),
                                        "upstream_unicode": identity.codepoints, "mapping_policy": "CODH v2 transcription; kyujitai and historical kana may be folded to modern codepoints",
                                        "source_collection": culture.source_collection, "source_uri": uri,
                                        "source_checksum": source_checksum, "asset_sha256": metadata.checksum,
                                        "dataset_version": "v2", "book_id": item.get("book_id"),
                                        "attribution": item.get("attribution", CODH_ATTRIBUTION),
                                        "license_text": "japanese/licenses/CC-BY-SA-4.0.txt", "processing": item.get("processing")})

    def _assets(self):
        for item in self.manifest.assets:
            path = safe_local(self.path.parent, item["file"])
            if path.stat().st_size > 40 * 1024 * 1024:
                raise ValueError("Excessive crop file")
            data = path.read_bytes()
            checksum = hashlib.sha256(data).hexdigest()
            if checksum != item["sha256"]:
                raise ValueError("Crop checksum mismatch")
            yield item, data, item.get("source_checksum", checksum)

    def _archives(self):
        for receipt in self.manifest.archives:
            path = safe_local(self.path.parent, receipt["file"])
            if path.stat().st_size > 10 * 1024**3 or sha256_file(path) != receipt["sha256"]:
                raise ValueError("Archive size or checksum mismatch")
            with zipfile.ZipFile(path) as archive:
                validate_archive(archive)
                for member in archive.infolist():
                    if not member.filename.endswith("_coordinate.csv"):
                        continue
                    book_id = Path(member.filename).stem.removesuffix("_coordinate")
                    if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", book_id):
                        raise ValueError("Invalid book ID")
                    book = receipt.get("books", {}).get(book_id, {})
                    with archive.open(member) as handle:
                        reader = csv.DictReader(io.TextIOWrapper(handle, encoding="utf-8-sig"))
                        if not {"Unicode", "Image", "X", "Y", "Width", "Height"}.issubset(reader.fieldnames or []):
                            raise ValueError("Invalid CODH coordinate CSV")
                        for row in reader:
                            if self.cancelled and self.cancelled():
                                raise InterruptedError("Historical import cancelled")
                            if not re.fullmatch(r"U\+[0-9A-Fa-f]{4,6}", row["Unicode"]):
                                raise ValueError("Invalid Unicode transcription")
                            scalar=int(row["Unicode"][2:],16)
                            if scalar>0x10FFFF or 0xD800<=scalar<=0xDFFF:
                                raise ValueError('Invalid Unicode scalar transcription')
                            character = chr(scalar)
                            if self.characters and character not in self.characters:
                                continue
                            if not re.fullmatch(r"[A-Za-z0-9_-]{1,120}", row["Image"]):
                                raise ValueError("Invalid page identifier")
                            x, y, width, height = [int(row[k]) for k in ["X", "Y", "Width", "Height"]]
                            if min(x, y) < 0 or min(width, height) < 1 or max(x, y, width, height) > 20000:
                                raise ValueError("Invalid bounding box")
                            crop = f"{book_id}/characters/{row['Unicode']}/{row['Unicode']}_{row['Image']}_X{x:04d}_Y{y:04d}.jpg"
                            try:
                                archive.getinfo(crop)
                            except KeyError:
                                raise ValueError("This archive has no display crops; use the full glyph archive")
                            item = {**book, "character": character, "file": crop, "page": row["Image"], "bbox": [x,y,width,height],
                                    "book_id": book_id, "variant_id": f"codh:v2:{row['Image']}:{row.get('Char ID', '')}:{x}:{y}",
                                    "source_uri": f"{CODH_URL}book/{book_id}/"}
                            item["culture"] = {"writing_tradition": "Japanese", "source_collection": "CODH 日本古典籍くずし字データセット", **book.get("culture", {}), "script": unicode_script(character)}
                            yield item, archive.read(crop), receipt["sha256"]

    def iter_records(self):
        from itertools import chain
        count = 0
        for item, data, checksum in chain(self._assets(), self._archives()):
            if self.cancelled and self.cancelled():
                raise InterruptedError("Historical import cancelled")
            if self.characters and item.get("character", item.get("identity", {}).get("text")) not in self.characters:
                continue
            if self.limit is not None and count >= self.limit:
                return
            yield self._record(item, data, checksum)
            count += 1
