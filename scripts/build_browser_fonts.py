"""Package licensed fonts and exact cmap coverage for browser-side typesetting.

Run with: python scripts/build_browser_fonts.py (requires fonttools and brotli).
"""
import json
from pathlib import Path
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[1]
source = ROOT / "samples/fonts"
target = ROOT / "apps/web/public/fonts"
target.mkdir(parents=True, exist_ok=True)
manifest = json.loads((source / "manifest.json").read_text(encoding="utf-8"))
entries = []
for entry in manifest["fonts"]:
    font = TTFont(source / entry["path"])
    coverage = "".join(chr(code) for code in sorted(font.getBestCmap()))
    font.flavor = "woff2"
    font.save(target / f'{entry["id"]}.woff2')
    entries.append({**{key: entry[key] for key in ["id", "family", "designer", "style", "license", "license_url", "rights"]}, "characters": coverage})
(target / "catalog.json").write_text(json.dumps(entries, ensure_ascii=False), encoding="utf-8")
print({item["family"]: len(item["characters"]) for item in entries})
