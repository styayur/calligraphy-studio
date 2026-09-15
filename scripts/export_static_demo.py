from __future__ import annotations

import argparse
import json
import shutil
import sqlite3
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def parse_json(value: str | None, fallback):
    if not value:
        return fallback
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return fallback


def safe_relative_asset(asset_url: str) -> str | None:
    prefix = "/assets/"
    if not asset_url.startswith(prefix):
        return None
    relative = asset_url[len(prefix) :]
    if ".." in Path(relative).parts:
        return None
    return relative


def export_database(database_path: Path, assets_dir: Path, output: Path) -> dict:
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    rows = connection.execute(
        """
        SELECT
          g.id, g.character, g.asset_url, g.asset_type, g.width, g.height, g.bbox,
          g.provenance_type, g.confidence, g.style_id, g.source_id,
          c.name AS calligrapher, s.name AS style, d.name AS dynasty,
          gs.dataset, gs.work, gs.license, gs.license_url, gs.rights
        FROM glyphs g
        LEFT JOIN calligraphers c ON c.id = g.calligrapher_id
        LEFT JOIN styles s ON s.id = g.style_id
        LEFT JOIN dynasties d ON d.id = g.dynasty_id
        JOIN glyph_sources gs ON gs.id = g.source_id
        ORDER BY g.created_at, g.id
        """
    ).fetchall()

    if output.exists():
        resolved_output = output.resolve()
        if PROJECT_ROOT not in resolved_output.parents:
            raise SystemExit(f"Refusing to replace output outside project: {resolved_output}")
        shutil.rmtree(resolved_output)
    (output / "assets").mkdir(parents=True)

    glyphs: list[dict] = []
    exported_ids: set[str] = set()
    styles: set[str] = set()
    dynasties: set[str] = set()
    calligraphers: set[str] = set()
    datasets: set[str] = set()
    sources: dict[tuple, dict] = {}

    for row in rows:
        rights = parse_json(row["rights"], {})
        if rights.get("redistribution_allowed") is not True:
            continue
        relative_asset = safe_relative_asset(row["asset_url"])
        if relative_asset is None:
            continue
        source_asset = (assets_dir / relative_asset).resolve()
        if assets_dir.resolve() not in source_asset.parents or not source_asset.is_file():
            continue
        destination = output / "assets" / relative_asset
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_asset, destination)

        glyph = {
            "id": row["id"],
            "character": row["character"],
            "source": {
                "dataset": row["dataset"],
                "calligrapher": row["calligrapher"],
                "style": row["style"],
                "dynasty": row["dynasty"],
                "work": row["work"],
                "license": row["license"],
                "license_url": row["license_url"],
                "rights": rights,
            },
            "asset": {
                "type": row["asset_type"],
                "url": f"demo/assets/{relative_asset}",
                "width": row["width"],
                "height": row["height"],
                "bbox": parse_json(row["bbox"], [0, 0, row["width"], row["height"]]),
            },
            "transform": {
                "x": 0,
                "y": 0,
                "scaleX": 1,
                "scaleY": 1,
                "rotation": 0,
                "skewX": 0,
                "skewY": 0,
            },
            "appearance": {"opacity": 1, "blendMode": "source-over"},
            "provenance": {
                "type": row["provenance_type"],
                "confidence": row["confidence"],
            },
        }
        glyphs.append(glyph)
        exported_ids.add(row["id"])
        if row["calligrapher"]:
            calligraphers.add(row["calligrapher"])
        if row["style"]:
            styles.add(row["style"])
        if row["dynasty"]:
            dynasties.add(row["dynasty"])
        datasets.add(row["dataset"])
        sources[(row["dataset"], row["work"])] = {
            "dataset": row["dataset"],
            "work": row["work"],
            "license": row["license"],
            "license_url": row["license_url"],
            "rights": rights,
        }

    meta = {
        "calligraphers": [{"id": index, "name": name} for index, name in enumerate(sorted(calligraphers), 1)],
        "styles": [{"id": index, "name": name} for index, name in enumerate(sorted(styles), 1)],
        "dynasties": [{"id": index, "name": name} for index, name in enumerate(sorted(dynasties), 1)],
        "datasets": sorted(datasets),
    }

    embedding_rows = connection.execute(
        """
        SELECT glyph_id, vector
        FROM glyph_embeddings
        WHERE model_name = 'visual-geometry-256-v1'
        """
    ).fetchall()
    vectors: dict[str, np.ndarray] = {}
    style_by_id: dict[str, int | None] = {}
    source_by_id: dict[str, int | None] = {}
    for row in rows:
        if row["id"] in exported_ids:
            style_by_id[row["id"]] = row["style_id"]
            source_by_id[row["id"]] = row["source_id"]
    for row in embedding_rows:
        if row["glyph_id"] in exported_ids:
            vectors[row["glyph_id"]] = np.frombuffer(row["vector"], dtype="<f4").astype(np.float32)

    similarity: dict[str, list[dict]] = {}
    ids = list(vectors)
    for target_id in ids:
        candidates = [
            candidate_id
            for candidate_id in ids
            if candidate_id != target_id
            and (
                style_by_id.get(target_id) is None
                or style_by_id.get(candidate_id) == style_by_id.get(target_id)
            )
        ]
        if not candidates:
            similarity[target_id] = []
            continue
        matrix = np.vstack([vectors[candidate_id] for candidate_id in candidates])
        scores = matrix @ vectors[target_id]
        count = min(12, len(candidates))
        best = np.argpartition(scores, -count)[-count:]
        best = best[np.argsort(scores[best])[::-1]]
        similarity[target_id] = [
            {"id": candidates[index], "score": round(float(scores[index]), 6)} for index in best
        ]

    (output / "glyphs.json").write_text(
        json.dumps(glyphs, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (output / "meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (output / "similarity.json").write_text(
        json.dumps(similarity, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    (output / "manifest.json").write_text(
        json.dumps(
            {
                "static_mode": True,
                "glyph_count": len(glyphs),
                "model_name": "visual-geometry-256-v1",
                "sources": list(sources.values()),
                "policy": "Only sources with redistribution_allowed=true are exported.",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    connection.close()
    return {"glyphs": len(glyphs), "sources": len(sources), "similarity": len(similarity)}


def copy_license_files(project_root: Path, output: Path) -> None:
    licenses = output / "licenses"
    licenses.mkdir(parents=True, exist_ok=True)
    candidates = {
        "nccu-mit.txt": project_root / "samples" / "cursive" / "raw" / "LICENSE",
        "arphic-public-license.txt": project_root / "third_party" / "hanzi-writer" / "ARPHICPL.TXT",
    }
    for destination_name, source in candidates.items():
        if source.is_file():
            shutil.copy2(source, licenses / destination_name)
    for source in (project_root / "samples" / "fonts" / "licenses").glob("*.txt"):
        shutil.copy2(source, licenses / source.name)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default=str(PROJECT_ROOT / "data" / "calligraphy.db"))
    parser.add_argument("--assets", default=str(PROJECT_ROOT / "storage" / "assets"))
    parser.add_argument("--output", default=str(PROJECT_ROOT / "apps" / "web" / "public" / "demo"))
    args = parser.parse_args()
    output = Path(args.output).resolve()
    result = export_database(Path(args.db).resolve(), Path(args.assets).resolve(), output)
    copy_license_files(PROJECT_ROOT, output)
    (PROJECT_ROOT / "apps" / "web" / "public" / ".nojekyll").write_text("", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
