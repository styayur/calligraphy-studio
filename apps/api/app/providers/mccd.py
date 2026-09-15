from __future__ import annotations

import csv
import io
import json
from collections.abc import Iterator, Mapping
from pathlib import Path
from typing import Any, Literal
from urllib.parse import urlparse

from app.providers.base import DatasetProvider, RawGlyphRecord

MCCD_LICENSE = "CC BY-NC-ND 4.0"
MCCD_LICENSE_URL = "https://creativecommons.org/licenses/by-nc-nd/4.0/"
MCCD_RIGHTS = {
    "commercial_use": False,
    "derivatives_allowed": False,
    "redistribution_allowed": False,
    "research_use": True,
}

FIELD_ALIASES: dict[str, tuple[str, ...]] = {
    "character": ("character", "char", "hanzi", "字", "汉字"),
    "asset": ("asset", "asset_url", "image", "image_path", "path", "file", "filename", "url"),
    "calligrapher": ("calligrapher", "author", "writer", "label_name", "书家", "书法家"),
    "style": ("style", "script", "script_style", "书体", "字体"),
    "dynasty": ("dynasty", "period", "朝代"),
    "work": ("work", "title", "piece", "作品", "碑帖"),
    "width": ("width", "w"),
    "height": ("height", "h"),
    "bbox": ("bbox", "box", "bounds"),
    "license": ("license", "license_name", "授权", "许可"),
    "license_url": ("license_url", "license_link"),
    "source_uri": ("source_uri", "source_url", "uri"),
    "dataset": ("dataset", "source", "data_source"),
    "provenance": ("provenance", "provenance_type", "glyph_origin"),
    "confidence": ("confidence", "provenance_confidence"),
}


def _clean(value: Any) -> str | None:
    if value is None:
        return None
    result = str(value).strip()
    return result or None


def _parse_int(value: Any) -> int | None:
    text = _clean(value)
    if text is None:
        return None
    try:
        return int(float(text))
    except ValueError:
        return None


def _parse_bbox(value: Any) -> list[float] | None:
    text = _clean(value)
    if text is None:
        return None
    if text.startswith("["):
        parsed = json.loads(text)
    else:
        parsed = [item.strip() for item in text.replace(";", ",").split(",")]
    if len(parsed) != 4:
        raise ValueError(f"bbox must contain four numbers, got: {value}")
    return [float(item) for item in parsed]


def _pick(row: Mapping[str, Any], field: str) -> Any:
    lowered = {str(key).strip().lower(): value for key, value in row.items()}
    for alias in FIELD_ALIASES[field]:
        if alias.lower() in lowered:
            return lowered[alias.lower()]
    return None


class MCCDManifestProvider(DatasetProvider):
    """Imports CSV, JSON, or JSONL manifests generated from an authorized MCCD download."""

    name = "mccd-manifest"

    def __init__(
        self,
        manifest_path: str | Path,
        dataset_root: str | Path | None = None,
        dataset_name: str = "MCCD",
        license_name: str = MCCD_LICENSE,
        license_url: str = MCCD_LICENSE_URL,
        rights: dict[str, bool] | None = None,
        characters: set[str] | None = None,
        limit: int | None = None,
    ) -> None:
        self.manifest_path = Path(manifest_path).resolve()
        self.dataset_root = (
            Path(dataset_root).resolve() if dataset_root else self.manifest_path.parent
        )
        self.dataset_name = dataset_name
        self.license_name = license_name
        self.license_url = license_url
        self.rights = dict(rights or MCCD_RIGHTS)
        self.characters = characters or set()
        self.limit = limit

    def _rows(self) -> Iterator[Mapping[str, Any]]:
        suffix = self.manifest_path.suffix.lower()
        if suffix == ".jsonl":
            with self.manifest_path.open("r", encoding="utf-8-sig") as handle:
                for line in handle:
                    if line.strip():
                        yield json.loads(line)
            return
        if suffix == ".json":
            payload = json.loads(self.manifest_path.read_text(encoding="utf-8-sig"))
            if isinstance(payload, dict):
                payload = payload.get("items", payload.get("records", []))
            if not isinstance(payload, list):
                raise ValueError("JSON manifest must be a list or contain an items/records list")
            yield from payload
            return

        sample = self.manifest_path.read_text(encoding="utf-8-sig")[:8192]
        dialect = csv.Sniffer().sniff(sample, delimiters=",\t;|")
        with self.manifest_path.open("r", encoding="utf-8-sig", newline="") as handle:
            yield from csv.DictReader(handle, dialect=dialect)

    def iter_records(self) -> Iterator[RawGlyphRecord]:
        emitted = 0
        for row_index, row in enumerate(self._rows(), start=1):
            character = _clean(_pick(row, "character"))
            if not character:
                raise ValueError(f"Manifest row {row_index} is missing a character")

            if self.characters and character not in self.characters:
                continue

            asset_value = _clean(_pick(row, "asset"))
            if not asset_value:
                raise ValueError(f"Manifest row {row_index} is missing an asset path or URL")

            parsed_url = urlparse(asset_value)
            asset_path: Path | None = None
            asset_url: str | None = None
            if parsed_url.scheme in {"http", "https"}:
                asset_url = asset_value
            else:
                asset_path = (self.dataset_root / asset_value).resolve()

            dataset = _clean(_pick(row, "dataset")) or self.dataset_name
            row_license = _clean(_pick(row, "license")) or self.license_name
            row_license_url = _clean(_pick(row, "license_url")) or self.license_url
            row_rights = dict(self.rights)
            if row_license != self.license_name and not row_license.startswith("CC BY-NC-ND"):
                row_rights = {
                    "commercial_use": None,
                    "derivatives_allowed": None,
                    "redistribution_allowed": None,
                    "research_use": None,
                }

            known_keys = {
                alias.lower()
                for aliases in FIELD_ALIASES.values()
                for alias in aliases
            }
            metadata = {
                str(key): value
                for key, value in row.items()
                if str(key).strip().lower() not in known_keys
            }

            yield RawGlyphRecord(
                character=character,
                dataset=dataset,
                calligrapher=_clean(_pick(row, "calligrapher")),
                style=_clean(_pick(row, "style")),
                dynasty=_clean(_pick(row, "dynasty")),
                work=_clean(_pick(row, "work")),
                asset_path=asset_path,
                asset_url=asset_url,
                original_filename=asset_path.name if asset_path else Path(parsed_url.path).name,
                width=_parse_int(_pick(row, "width")),
                height=_parse_int(_pick(row, "height")),
                bbox=_parse_bbox(_pick(row, "bbox")),
                license=row_license,
                license_url=row_license_url,
                source_uri=_clean(_pick(row, "source_uri")),
                rights=row_rights,
                provenance_type=_clean(_pick(row, "provenance")) or "original",
                confidence=float(_pick(row, "confidence")) if _clean(_pick(row, "confidence")) else None,
                metadata=metadata,
                source_index=row_index,
            )
            emitted += 1
            if self.limit is not None and emitted >= self.limit:
                return


AttributeMode = Literal["four-task", "character", "style", "dynasty", "calligrapher"]


class MCCDLmdbProvider(DatasetProvider):
    """Reads MCCD's documented image-*/label-* LMDB layout without loading torch."""

    name = "mccd-lmdb"

    def __init__(
        self,
        lmdb_path: str | Path,
        attribute_mode: AttributeMode = "four-task",
        maps: dict[str, dict[str, str]] | None = None,
        dataset_name: str = "MCCD",
        license_name: str = MCCD_LICENSE,
        license_url: str = MCCD_LICENSE_URL,
        rights: dict[str, bool] | None = None,
        characters: set[str] | None = None,
        limit: int | None = None,
    ) -> None:
        self.lmdb_path = Path(lmdb_path).resolve()
        self.attribute_mode = attribute_mode
        self.maps = maps or {}
        self.dataset_name = dataset_name
        self.license_name = license_name
        self.license_url = license_url
        self.rights = dict(rights or MCCD_RIGHTS)
        self.characters = characters or set()
        self.limit = limit

    @staticmethod
    def _text(txn: Any, key: str) -> str | None:
        value = txn.get(key.encode("ascii"))
        return value.decode("utf-8") if value is not None else None

    def _resolve(self, field: str, value: str | None) -> str | None:
        if value is None:
            return None
        field_map = self.maps.get(field, {})
        resolved = field_map.get(value, field_map.get(str(value)))
        if resolved is not None:
            return resolved
        if value.strip().lstrip("-").isdigit():
            raise ValueError(
                f"Unresolved indexed {field} label {value}; provide it through --maps"
            )
        return value

    def iter_records(self) -> Iterator[RawGlyphRecord]:
        try:
            import lmdb
        except ImportError as exc:
            raise RuntimeError("LMDB support requires `pip install lmdb`") from exc

        env = lmdb.open(
            str(self.lmdb_path),
            subdir=self.lmdb_path.is_dir(),
            readonly=True,
            lock=False,
            readahead=False,
            meminit=False,
            max_readers=8,
        )
        emitted = 0
        try:
            with env.begin(write=False) as txn:
                raw_count = txn.get(b"num-samples")
                if raw_count is None:
                    raise ValueError("LMDB is missing the num-samples key")
                total = int(raw_count.decode("ascii"))

            for index in range(1, total + 1):
                with env.begin(write=False) as txn:
                    image = txn.get(f"image-{index:09d}".encode("ascii"))
                    if image is None:
                        continue

                    label = self._text(txn, f"label-{index:09d}")
                    char_value = self._text(txn, f"char-{index:09d}")
                    style_value = self._text(txn, f"style-{index:09d}")
                    dynasty_value = self._text(txn, f"dynasty-{index:09d}")
                    calligrapher_value = self._text(txn, f"calligrapher-{index:09d}")

                character: str | None = None
                style: str | None = None
                dynasty: str | None = None
                calligrapher: str | None = None

                if self.attribute_mode == "four-task":
                    character = self._resolve("character", char_value or label)
                    style = self._resolve("style", style_value)
                    dynasty = self._resolve("dynasty", dynasty_value)
                    calligrapher = self._resolve(
                        "calligrapher", calligrapher_value or (label if char_value else None)
                    )
                elif self.attribute_mode == "character":
                    character = self._resolve("character", char_value or label)
                elif self.attribute_mode == "style":
                    style = self._resolve("style", style_value or label)
                elif self.attribute_mode == "dynasty":
                    dynasty = self._resolve("dynasty", dynasty_value or label)
                elif self.attribute_mode == "calligrapher":
                    calligrapher = self._resolve("calligrapher", calligrapher_value or label)

                if not character:
                    raise ValueError(
                        f"LMDB sample {index} has no resolved character; "
                        "provide --character-map for indexed labels"
                    )
                if self.characters and character not in self.characters:
                    continue

                yield RawGlyphRecord(
                    character=character,
                    dataset=self.dataset_name,
                    calligrapher=calligrapher,
                    style=style,
                    dynasty=dynasty,
                    asset_bytes=image,
                    original_filename=f"mccd-{index:09d}.png",
                    license=self.license_name,
                    license_url=self.license_url,
                    rights=dict(self.rights),
                    metadata={
                        "lmdb_index": index,
                        "lmdb_label": label,
                        "attribute_mode": self.attribute_mode,
                    },
                    source_index=index,
                )
                emitted += 1
                if self.limit is not None and emitted >= self.limit:
                    return
        finally:
            env.close()