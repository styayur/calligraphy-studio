"""Measure bundled Japanese cmap coverage against pinned reviewed repertoires."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[1]


def report() -> dict:
    fixture = json.loads((ROOT / "tests/fixtures/japanese-repertoires.json").read_text(encoding="utf-8"))
    entries = json.loads((ROOT / "samples/fonts/japanese/manifest.json").read_text(encoding="utf-8"))["fonts"]
    coverage = {}
    for entry in entries:
        path = ROOT / "samples/fonts/japanese" / entry["path"]
        with TTFont(path) as font:
            coverage[entry["id"]] = set(font.getBestCmap())
    yuji = set().union(*(coverage[e["id"]] for e in entries if e["id"].startswith("yuji-")))
    klee = coverage["klee-one"]
    fallback = coverage["jp-coverage-serif"]
    groups = {"Yuji": yuji, "Klee One": klee, "Coverage fallback": fallback,
              "Combined Japanese library": yuji | klee | fallback}
    result = {"source": {key: fixture[key] for key in ["unicode_version", "source_url", "source_sha256", "notes"]},
              "fonts": {e["id"]: {"sha256": e["sha256"], "original_sha256": e.get("original_sha256"),
                                    "upstream_commit": e.get("upstream_commit"), "font_version": e.get("font_version"),
                                    "license": e.get("license"), "source_role": e.get("source_role"),
                                    "bytes": (ROOT / "samples/fonts/japanese" / e["path"]).stat().st_size}
                        for e in entries}, "repertoires": {}}
    for name, text in fixture["repertoires"].items():
        target = {ord(char) for char in text}
        result["repertoires"][name] = {
            "total": len(target),
            "covered": {group: len(target & chars) for group, chars in groups.items()},
            "remaining_missing": "".join(chr(cp) for cp in sorted(target - groups["Combined Japanese library"])),
        }
    return result


def markdown(data: dict) -> str:
    labels = {"joyo_2010": "Jōyō 2010", "jinmeiyo_2010": "Jinmeiyō 2010",
              "jis_x_0208_kanji": "JIS X 0208 kanji", "jis_x_0213_kanji": "JIS X 0213 kanji",
              "reviewed_project_corpus": "Reviewed project corpus"}
    lines = ["# Japanese coverage benchmark", "",
             "This measures Unicode codepoint coverage in bundled Japanese fonts; it does not assess visual quality,",
             "regional glyph accuracy per character, or complete Japanese typography. The fallback is a renamed,",
             "OFL-licensed subset derived from Source Han Serif JP, and is never labelled a manuscript.", "",
             "The Jōyō 2010, Jinmeiyō, JIS X 0208 kanji and JIS X 0213 kanji sets come from",
             f"[Unicode Unihan {data['source']['unicode_version']}]({data['source']['source_url']})",
             f"(`SHA-256 {data['source']['source_sha256']}`). The JIS properties count ideographs only;",
             "they do not cover each standard's punctuation, kana or multi-codepoint sequences.",
             "JIS X 0213 here is the union of Unihan `kJis0` and `kJIS0213`, including its JIS X 0208 base.",
             "The reviewed project corpus is a separately labelled fixture from the existing Japanese examples",
             "and selected uncommon characters. Jinmeiyō includes Unihan-marked variants.", "",
             "| Repertoire | Total | Yuji | Klee One | Coverage fallback | Combined | Remaining missing |",
             "| --- | ---: | ---: | ---: | ---: | ---: | --- |"]
    for name, item in data["repertoires"].items():
        covered = item["covered"]
        lines.append(f"| {labels[name]} | {item['total']} | {covered['Yuji']} | {covered['Klee One']} | {covered['Coverage fallback']} | {covered['Combined Japanese library']} | {item['remaining_missing'] or 'None'} |")
    lines += ["", "The fallback intentionally contains only characters absent from both Yuji and Klee in the",
              "pinned target sets. Its standalone column is therefore small by design. Ordinary composition",
              "prefers Yuji and Klee; strict Japanese mode can use the fallback without Chinese substitution.", "",
              "The two new compressed runtime fonts add 6,578,155 bytes (Klee 4,746,784; coverage subset 1,831,371).",
              "The source OTF is 24,574,024 bytes and is not bundled in platform packages.", "",
              "Reproduce from pinned upstream binaries and Unihan data:", "",
              "```sh", "python scripts/build_japanese_coverage.py --fetch", "python scripts/build_browser_fonts.py",
              "python scripts/report_japanese_coverage.py --write", "```", "",
              "The font build script verifies original SHA-256 hashes, preserves HarfBuzz layout features,",
              "renames the derivative's reserved font family, and checks its SHA-256 against the pinned font manifest.",
              "The JSON report beside this file contains exact per-font checksums and all remaining missing characters.", ""]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    data = report()
    json_text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    markdown_text = markdown(data)
    paths = {ROOT / "docs/JAPANESE_COVERAGE.json": json_text,
             ROOT / "docs/JAPANESE_COVERAGE.md": markdown_text}
    for path, content in paths.items():
        if args.write:
            path.write_text(content, encoding="utf-8", newline="\n")
        elif path.read_text(encoding="utf-8") != content:
            raise ValueError(f"Stale coverage report: {path}")
    for name, item in data["repertoires"].items():
        print(name, item["covered"], "missing", item["remaining_missing"] or "none")


if __name__ == "__main__":
    main()
