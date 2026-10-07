"""Reproduce the Japanese coverage fixture and the OFL fallback subset.

Run with --fetch to retrieve pinned upstream files into ignored work/. The
committed subset and fixture are sufficient for ordinary offline builds.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import urllib.request
import zipfile
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "work/font-upstream"
KLEE_COMMIT = "8b0532731b63ad8a445ca341d8d7d941079b83ab"
SOURCE_COMMIT = "7889f11bf31170b5d092a083b357c8c8130f89e0"  # 2.003R
UPSTREAM = {
    "KleeOne-Regular.ttf": (
        f"https://raw.githubusercontent.com/fontworks-fonts/Klee/{KLEE_COMMIT}/fonts/ttf/KleeOne-Regular.ttf",
        "74cb0a6523cc22b221ceaa7b78b56cea66512ec14b4145fd0102ffe27c30d084",
    ),
    "SourceHanSerif-Regular.otf": (
        f"https://raw.githubusercontent.com/adobe-fonts/source-han-serif/{SOURCE_COMMIT}/OTF/Japanese/SourceHanSerif-Regular.otf",
        "066dfd35dbcb96f953ebd72eb182169c3cec6b7c0f18be22f1b6e3936ac6ac20",
    ),
    "Unihan-16.0.0.zip": (
        "https://www.unicode.org/Public/16.0.0/ucd/Unihan.zip",
        "b8f000df69de7828d21326a2ffea462b04bc7560022989f7cc704f10521ef3e0",
    ),
    "Klee-OFL.txt": (
        f"https://raw.githubusercontent.com/fontworks-fonts/Klee/{KLEE_COMMIT}/OFL.txt",
        "e376b0df8e8a2345a9533db6f0a5333a1107975569ad9d1973a7ee557161ca38",
    ),
    "SourceHanSerif-LICENSE.txt": (
        f"https://raw.githubusercontent.com/adobe-fonts/source-han-serif/{SOURCE_COMMIT}/LICENSE.txt",
        "9ff5bb567e1b92c801fc1069e5fbf992ff8efccacb9db94e5959a5b3ba9bb903",
    ),
}
REPERTOIRE_KEYS = {
    "joyo_2010": "kJoyoKanji",
    "jinmeiyo_2010": "kJinmeiyoKanji",
    "jis_x_0208_kanji": "kJis0",
    "jis_x_0213_kanji": "kJIS0213",
}
# Existing Japanese manifest and browser examples, plus reviewed uncommon
# characters. This is a project fixture, not an official national repertoire.
CORPUS = "日本語漢字書道国國学學春海明月山水清風鳥龍辻骨𠮟塡剝頰鬱𠮷あいうえおアイウエオカナ、。「」ー"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def upstream_files(fetch: bool) -> None:
    CACHE.mkdir(parents=True, exist_ok=True)
    for name, (url, expected) in UPSTREAM.items():
        path = CACHE / name
        if fetch and not path.exists():
            request = urllib.request.Request(url, headers={"User-Agent": "CalligraphyStudio-font-reproduction/0.7"})
            with urllib.request.urlopen(request, timeout=90) as response:
                if response.url != url:
                    raise ValueError(f"Unexpected upstream redirect for {name}")
                path.write_bytes(response.read(50 * 1024 * 1024 + 1))
        if not path.is_file():
            raise FileNotFoundError(f"Run with --fetch to obtain {name}")
        if expected and sha(path) != expected:
            raise ValueError(f"Upstream checksum mismatch: {name}")


def repertoires() -> dict[str, set[int]]:
    result = {name: set() for name in REPERTOIRE_KEYS}
    by_property = {value: key for key, value in REPERTOIRE_KEYS.items()}
    with zipfile.ZipFile(CACHE / "Unihan-16.0.0.zip") as archive:
        for line in archive.read("Unihan_OtherMappings.txt").decode("utf-8").splitlines():
            if not line.startswith("U+"):
                continue
            codepoint, prop, value = line.split("\t")
            name = by_property.get(prop)
            if name and (name != "joyo_2010" or value == "2010"):
                result[name].add(int(codepoint[2:], 16))
    if [len(result[name]) for name in REPERTOIRE_KEYS] != [2136, 863, 6356, 3695]:
        raise ValueError("Pinned Unihan repertoire counts changed")
    # Unihan marks the 0213 additions separately; plane 1 includes JIS X 0208.
    result["jis_x_0213_kanji"].update(result["jis_x_0208_kanji"])
    result["reviewed_project_corpus"] = {ord(c) for c in CORPUS}
    return result


def cmap(path: Path) -> set[int]:
    with TTFont(path) as font:
        return set(font.getBestCmap())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fetch", action="store_true")
    args = parser.parse_args()
    upstream_files(args.fetch)
    sets = repertoires()
    fixture = {
        "unicode_version": "16.0.0",
        "source_url": UPSTREAM["Unihan-16.0.0.zip"][0],
        "source_sha256": UPSTREAM["Unihan-16.0.0.zip"][1],
        "notes": "JIS properties count ideographs mapped by Unihan, not all JIS punctuation or kana. Jinmeiyo includes Unihan-marked variants.",
        "repertoires": {name: "".join(chr(cp) for cp in sorted(values)) for name, values in sets.items()},
    }
    target = ROOT / "tests/fixtures/japanese-repertoires.json"
    target.write_text(json.dumps(fixture, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    yuji = set()
    for path in sorted((ROOT / "samples/fonts/japanese/yuji").glob("*.ttf")):
        yuji.update(cmap(path))
    klee_path = ROOT / "samples/fonts/japanese/klee/KleeOne-Regular.ttf"
    klee_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(CACHE / "KleeOne-Regular.ttf", klee_path)
    klee = cmap(klee_path)
    source = CACHE / "SourceHanSerif-Regular.otf"
    source_cmap = cmap(source)
    target_codes = set().union(*sets.values()) - yuji - klee
    missing_upstream = target_codes - source_cmap
    if missing_upstream:
        raise ValueError(f"Source Han Serif JP lacks {len(missing_upstream)} target characters")
    font = TTFont(source)
    font.recalcTimestamp = False
    options = subset.Options()
    options.layout_features = ["*"]  # keep locl / vert / vrt2 for HarfBuzz
    options.name_IDs = ["*"]
    options.name_languages = ["*"]
    options.notdef_glyph = True
    options.recommended_glyphs = True
    worker = subset.Subsetter(options=options)
    worker.populate(unicodes=target_codes)
    worker.subset(font)
    # The upstream OFL reserves "Source". Rename this modified font internally.
    names = font["name"]
    for record in names.names:
        if record.nameID in {1, 4, 16}:
            value = "Calligraphy JP Coverage Serif"
        elif record.nameID == 3:
            value = "Calligraphy JP Coverage Serif 2.003 subset"
        elif record.nameID == 6:
            value = "CalligraphyJPCoverageSerif-Regular"
        else:
            continue
        names.setName(value, record.nameID, record.platformID, record.platEncID, record.langID)
    output = ROOT / "samples/fonts/japanese/coverage/CalligraphyJPCoverageSerif-Regular.otf"
    output.parent.mkdir(parents=True, exist_ok=True)
    font.save(output)
    subset_cmap = cmap(output)
    if not target_codes <= subset_cmap:
        raise ValueError("Generated subset lost target coverage")
    manifest = json.loads((ROOT / "samples/fonts/japanese/manifest.json").read_text(encoding="utf-8"))
    pinned_subset = next(e for e in manifest["fonts"] if e["id"] == "jp-coverage-serif")
    if sha(output) != pinned_subset["sha256"]:
        raise ValueError("Generated subset differs from pinned SHA-256; check fontTools version")
    for family, upstream_name in [("klee", "Klee-OFL.txt"), ("source-han-serif", "SourceHanSerif-LICENSE.txt")]:
        destination = ROOT / f"third_party/japanese/{family}/OFL.txt"
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(CACHE / upstream_name, destination)
    print(json.dumps({"klee_sha256": sha(klee_path), "subset_sha256": sha(output),
                      "source_sha256": sha(source), "subset_bytes": output.stat().st_size,
                      "subset_characters": len(target_codes), "target_characters": len(set().union(*sets.values()))}, indent=2))


if __name__ == "__main__":
    main()
