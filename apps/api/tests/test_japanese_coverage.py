"""Regression gates for Japanese-only coverage and additive v0.7.0 compatibility."""
import hashlib
import json
from pathlib import Path

from fontTools.ttLib import TTFont

from app.providers.font_manifest import FontManifestProvider
from app.schemas import ProjectDocument
from app.services.font_shaper import FontShaper

ROOT = Path(__file__).resolve().parents[3]
JP = ROOT / "samples/fonts/japanese/manifest.json"


def test_reviewed_repertoires_and_font_checksums():
    fixture = json.loads((ROOT / "tests/fixtures/japanese-repertoires.json").read_text(encoding="utf-8"))
    report = json.loads((ROOT / "docs/JAPANESE_COVERAGE.json").read_text(encoding="utf-8"))
    entries = json.loads(JP.read_text(encoding="utf-8"))["fonts"]
    maps = {}
    for entry in entries:
        path = JP.parent / entry["path"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == entry["sha256"]
        with TTFont(path) as font:
            maps[entry["id"]] = set(font.getBestCmap())
    yuji = set().union(*(maps[e["id"]] for e in entries if e["id"].startswith("yuji-")))
    klee, fallback = maps["klee-one"], maps["jp-coverage-serif"]
    assert len(fixture["repertoires"]["joyo_2010"]) == 2136
    assert len(fixture["repertoires"]["jinmeiyo_2010"]) == 863
    assert len(fixture["repertoires"]["jis_x_0208_kanji"]) == 6356
    assert len(fixture["repertoires"]["jis_x_0213_kanji"]) == 10051
    assert fixture["source_sha256"] == "b8f000df69de7828d21326a2ffea462b04bc7560022989f7cc704f10521ef3e0"
    for name, text in fixture["repertoires"].items():
        target = set(map(ord, text))
        assert target <= yuji | klee | fallback, name
        assert report["repertoires"][name]["covered"]["Yuji"] == len(target & yuji)
        assert report["repertoires"][name]["covered"]["Combined Japanese library"] == len(target)
    assert ord("㐆") not in yuji | klee and ord("㐆") in fallback
    assert ord("骨") in yuji & klee
    assert fallback.isdisjoint(yuji | klee)
    jis = set(map(ord, fixture["repertoires"]["jis_x_0213_kanji"]))
    assert len(jis & yuji) >= 6745 and len(jis & klee) >= 7680
    assert len(jis & fallback) >= 2359


def test_fallback_is_japanese_font_with_exportable_rights_and_vertical_shaping(client):
    manifest = json.loads(JP.read_text(encoding="utf-8"))["fonts"]
    fallback = next(e for e in manifest if e["id"] == "jp-coverage-serif")
    assert fallback["source_role"] == "coverage-fallback"
    assert fallback["locale"] == "ja-JP" and fallback["writing_tradition"] == "Japanese"
    assert fallback["license"] == "OFL-1.1" and fallback["original_sha256"]
    assert (ROOT / "apps/web/public" / fallback["bundle_license_text"]).is_file()
    records = list(FontManifestProvider(JP, characters={"㐆"}).iter_records())
    assert len(records) == 1
    record = records[0]
    assert record.provenance_type == "font" and record.culture["writing_tradition"] == "Japanese"
    assert record.metadata["source_role"] == "coverage-fallback"
    assert record.metadata["license_text"] == fallback["bundle_license_text"]
    shaped = FontShaper(JP.parent / fallback["path"]).shape("㐆", locale="ja-JP", vertical=True)
    assert shaped and shaped[1]["direction"] == "ttb" and shaped[1]["features"]["vert"] == 1
    response = client.post("/api/compose/batch", json={"text": "㐆", "writing_tradition": "Japanese", "locale": "ja-JP", "layout": "vertical-rtl"})
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["resolved_characters"] == 1 and not result["missing"]
    glyph = result["placements"][0]["glyph"]
    assert glyph["source"]["source_role"] == "coverage-fallback"
    assert glyph["source"]["license"] == "OFL-1.1"
    assert glyph["source"]["writing_tradition"] == "Japanese"
    assert glyph["metadata"]["original_sha256"] == fallback["original_sha256"]
    assert glyph["metadata"]["shaping"]["direction"] == "ttb"
    chinese = client.get("/api/glyphs", params={"character": "㐆", "writing_tradition": "Chinese"})
    assert chinese.status_code == 200 and not chinese.json()["items"]


def test_klee_and_yuji_coexist_and_legacy_project_loads():
    records = list(FontManifestProvider(JP, characters={"骨"}).iter_records())
    assert {r.metadata["font_id"] for r in records} >= {"yuji-syuku", "klee-one"}
    assert len({r.variant["id"] for r in records}) == len(records)
    assert all(r.provenance_type == "font" and r.identity["locale"] == "ja-JP" for r in records)
    legacy = ROOT / "tests/fixtures/projects/v2-japanese-modern.json"
    assert ProjectDocument.model_validate_json(legacy.read_text(encoding="utf-8")).version == 2
