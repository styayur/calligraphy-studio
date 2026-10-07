"""Build every platform's catalog from the canonical manifest, fully offline.

Chinese WOFF2 assets stay unchanged. Japanese fonts use gzip of the unmodified
upstream TTF for portable HarfBuzz WASM shaping.
"""
import gzip
import hashlib
import json
import shutil
from pathlib import Path
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[1]


def main():
    canonical = ROOT / "samples/asset-manifest.json"
    manifest = json.loads(canonical.read_text(encoding="utf-8"))
    target = ROOT / "apps/web/public/fonts"
    target.mkdir(parents=True, exist_ok=True)
    (target / "licenses").mkdir(exist_ok=True)
    entries, provenance = [], []
    for pack in manifest["font_packs"]:
        source = ROOT / "samples" / pack
        for entry in json.loads(source.read_text(encoding="utf-8"))["fonts"]:
            if not entry.get("enabled", True):
                continue
            if entry["rights"].get("redistribution_allowed") is not True:
                raise ValueError(f"Refusing to bundle {entry['id']}")
            original = source.parent / entry["path"]
            raw = original.read_bytes()
            checksum = hashlib.sha256(raw).hexdigest()
            if checksum != entry["sha256"]:
                raise ValueError(f"Font checksum mismatch: {entry['id']}")
            with TTFont(original) as font:
                coverage = "".join(chr(c) for c in sorted(font.getBestCmap()))
                if entry.get("language") == "ja":
                    # AAPT transparently decompresses/renames *.gz assets. Preserve the
                    # exact compressed bytes and manifest URI on Android with *.gzip.
                    file = f"{entry['id']}{original.suffix}.gzip"
                    legacy = target / f"{entry['id']}.ttf.gz"
                    if legacy.is_file() and legacy.resolve().parent == target.resolve():
                        legacy.unlink()
                    compressed = target / file
                    if not compressed.exists() or gzip.decompress(compressed.read_bytes()) != raw:
                        compressed.write_bytes(gzip.compress(raw, compresslevel=9, mtime=0))
                    renderer = "harfbuzz"
                else:
                    file = f"{entry['id']}.woff2"
                    if not (target / file).exists():
                        font.flavor = "woff2"
                        font.save(target / file)
                    renderer = "browser-legacy"
            if entry.get("language") == "ja" and entry["id"].startswith("yuji-"):
                license_path = ROOT / "third_party/japanese/yuji/OFL.txt"
            else:
                license_path = source.parent / entry["license_text"]
            license_file = f"licenses/OFL-{entry['id']}.txt"
            shutil.copyfile(license_path, target / license_file)
            record = {**entry, "path": file, "renderer": renderer, "characters": coverage,
                      "license_text": f"fonts/{license_file}",
                      "runtime_sha256": hashlib.sha256((target / file).read_bytes()).hexdigest()}
            entries.append(record)
            provenance.append({"id": entry["id"], "original": {"path": original.relative_to(ROOT).as_posix(), "sha256": checksum},
                               "runtime": {"path": f"apps/web/public/fonts/{file}", "sha256": record["runtime_sha256"]},
                               "source_uri": entry["source_uri"], "upstream_commit": entry.get("upstream_commit"),
                               "license": entry["license"], "license_text": record["license_text"],
                               "source_role": entry.get("source_role"), "original_sha256": entry.get("original_sha256"),
                               "subset_command": entry.get("subset_command")})
    (target / "catalog.json").write_text(json.dumps(entries, ensure_ascii=False), encoding="utf-8", newline="\n")
    # Git stores this text as LF; universal-newline reading also handles an older
    # Windows working copy that predates the repository's .gitattributes rules.
    canonical_bytes = canonical.read_text(encoding="utf-8").encode("utf-8")
    (target / "asset-manifest.json").write_text(json.dumps({**manifest, "canonical_sha256": hashlib.sha256(canonical_bytes).hexdigest(), "fonts": provenance}, indent=2), encoding="utf-8", newline="\n")
    shutil.copyfile(ROOT / 'LICENSE', target.parent / 'LICENSE')
    shutil.copyfile(ROOT / 'third_party/NOTICE.md', target.parent / 'THIRD_PARTY_NOTICE.md')
    (target.parent / 'licenses').mkdir(exist_ok=True)
    for name in ['HarfBuzz-COPYING.txt','harfbuzzjs-MIT.txt']:
        shutil.copyfile(ROOT / 'third_party/harfbuzz' / name, target.parent / 'licenses' / name)
    print({e["family"]: {"characters": len(e["characters"]), "bytes": (target / e["path"]).stat().st_size} for e in entries})


if __name__ == "__main__":
    main()
