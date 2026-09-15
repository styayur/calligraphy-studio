from __future__ import annotations

import io
from pathlib import Path

import lmdb
import pytest
from PIL import Image

from app.providers.mccd import MCCDLmdbProvider
from app.utils.image_meta import inspect_asset_bytes


def _png_bytes() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (64, 80), "white").save(buffer, format="PNG")
    return buffer.getvalue()


def test_svg_metadata() -> None:
    data = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 600"><rect/></svg>'
    metadata = inspect_asset_bytes(data, filename="glyph.svg")
    assert metadata.asset_type == "svg"
    assert metadata.width == 512
    assert metadata.height == 600
    assert metadata.bbox == [0.0, 0.0, 512.0, 600.0]


def test_lmdb_provider_maps_indexed_attributes(tmp_path: Path) -> None:
    lmdb_path = tmp_path / "mccd"
    env = lmdb.open(str(lmdb_path), map_size=8 * 1024 * 1024)
    with env.begin(write=True) as txn:
        txn.put(b"num-samples", b"1")
        txn.put(b"image-000000001", _png_bytes())
        txn.put(b"label-000000001", b"7")
        txn.put(b"char-000000001", b"23")
        txn.put(b"style-000000001", b"2")
        txn.put(b"dynasty-000000001", b"4")
    env.close()

    provider = MCCDLmdbProvider(
        lmdb_path,
        attribute_mode="four-task",
        maps={
            "character": {"23": "山"},
            "style": {"2": "行书"},
            "dynasty": {"4": "东晋"},
            "calligrapher": {"7": "王羲之"},
        },
    )
    records = list(provider.iter_records())
    assert len(records) == 1
    assert records[0].character == "山"
    assert records[0].calligrapher == "王羲之"
    assert records[0].style == "行书"
    assert records[0].dynasty == "东晋"
    assert records[0].asset_bytes


def test_nccu_cursive_provider(tmp_path: Path) -> None:
    from app.providers.nccu_cursive import NCCUCursiveProvider

    project_root = Path(__file__).resolve().parents[3]
    records = list(
        NCCUCursiveProvider(
            dataset_root=project_root / "samples" / "cursive" / "raw",
            split="Test",
            characters={"春", "山"},
            limit_per_character=2,
        ).iter_records()
    )
    assert len(records) == 4
    assert {record.character for record in records} == {"春", "山"}
    assert all(record.style == "草书" for record in records)
    assert all(record.license == "MIT" for record in records)


def test_hanzi_writer_provider_from_cache(tmp_path: Path) -> None:
    from app.providers.hanzi_writer import HanziWriterProvider

    cache = tmp_path / "hanzi"
    cache.mkdir()
    (cache / "山.json").write_text(
        '{"strokes":["M 100 100 L 900 100 L 900 900 Z"],"medians":[]}',
        encoding="utf-8",
    )
    records = list(
        HanziWriterProvider("山", cache_dir=cache, fetch_remote=False).iter_records()
    )
    assert len(records) == 1
    assert records[0].provenance_type == "fallback"
    assert records[0].asset_bytes
    assert b"<svg" in records[0].asset_bytes


def test_ofl_font_manifest_provider() -> None:
    from app.providers.font_manifest import FontManifestProvider

    project_root = Path(__file__).resolve().parents[3]
    records = list(
        FontManifestProvider(
            project_root / "samples" / "fonts" / "manifest.json",
            characters=set("山水草行楷"),
        ).iter_records()
    )
    assert len(records) == 15
    assert {record.style for record in records} == {"楷书", "行书", "草书"}
    assert all(record.provenance_type == "font" for record in records)
    assert all(record.license == "OFL-1.1" for record in records)
    assert all(record.asset_bytes for record in records)


def test_font_manifest_noncommercial_filter(tmp_path: Path) -> None:
    from app.providers.font_manifest import FontManifestProvider

    project_root = Path(__file__).resolve().parents[3]
    font_path = project_root / "samples" / "fonts" / "ofl" / "mashanzheng" / "MaShanZheng-Regular.ttf"
    manifest = tmp_path / "noncommercial.json"
    manifest.write_text(
        __import__("json").dumps(
            {
                "fonts": [
                    {
                        "id": "local-nc-font",
                        "family": "Local NC Font",
                        "style": "楷书",
                        "path": str(font_path),
                        "characters": "山",
                        "license": "User-provided non-commercial license",
                        "rights": {
                            "commercial_use": False,
                            "derivatives_allowed": False,
                            "redistribution_allowed": False,
                        },
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    assert list(
        FontManifestProvider(manifest, characters={"山"}, include_noncommercial=False).iter_records()
    ) == []
    records = list(
        FontManifestProvider(manifest, characters={"山"}, include_noncommercial=True).iter_records()
    )
    assert len(records) == 1
    assert records[0].rights["commercial_use"] is False
    assert records[0].provenance_type == "font"
