from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen

REPO = "nccuviplab/CursiveChineseCalligraphyDataset"
BRANCH = "master"
DATASET_ROOT = "Cursive_Chinese_Calligraphy_Dataset"
LICENSE_TEXT = """MIT License

Copyright (c) 2019 VIPLab of Dept. Computer Science of National Chengchi University, Taipei, Taiwan

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""


def request_bytes(url: str) -> bytes:
    request = Request(url, headers={"User-Agent": "CalligraphyStudio/0.2"})
    with urlopen(request, timeout=60) as response:  # noqa: S310
        return response.read()


def base_character(name: str) -> str:
    return re.sub(r"\d+$", "", name).strip()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--characters", default="春眠不觉晓处闻啼鸟山重水复疑无路柳暗花明又一村")
    parser.add_argument("--split", default="Test", choices=["Training", "Validation", "Test"])
    parser.add_argument("--variants", type=int, default=2)
    parser.add_argument("--output", default="samples/cursive/raw")
    args = parser.parse_args()

    requested = {character for character in args.characters if not character.isspace()}
    output = Path(args.output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    (output / "LICENSE").write_text(LICENSE_TEXT, encoding="utf-8")

    tree_url = f"https://api.github.com/repos/{REPO}/git/trees/{BRANCH}?recursive=1"
    tree = json.loads(request_bytes(tree_url).decode("utf-8"))["tree"]
    prefix = f"{DATASET_ROOT}/{args.split}/"
    files_by_character: dict[str, list[str]] = {}
    for item in tree:
        item_path = item["path"]
        if item["type"] != "blob" or not item_path.startswith(prefix):
            continue
        relative = item_path.removeprefix(prefix)
        parts = relative.split("/")
        if len(parts) != 2:
            continue
        directory_name, filename = parts
        if not filename.lower().endswith((".jpg", ".jpeg", ".png")):
            continue
        if filename.startswith("gen_"):
            continue
        character = base_character(directory_name)
        if character in requested:
            files_by_character.setdefault(character, []).append(item_path)

    downloaded: list[dict] = []
    for character in sorted(requested):
        chosen = sorted(set(files_by_character.get(character, [])))
        # Prefer un-suffixed directories before numeric variants while preserving variants.
        chosen.sort(key=lambda value: (base_character(Path(value).parent.name) != Path(value).parent.name, value))
        chosen = chosen[: args.variants]
        if not chosen:
            print(f"missing: {character}")
            continue
        for remote_path in chosen:
            relative = Path(remote_path).relative_to(DATASET_ROOT)
            destination = output / DATASET_ROOT / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            raw_url = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/{quote(remote_path, safe='/')}"
            destination.write_bytes(request_bytes(raw_url))
            downloaded.append(
                {
                    "character": character,
                    "path": destination.relative_to(output).as_posix(),
                    "source_path": remote_path,
                    "source_url": raw_url,
                }
            )
            print(f"downloaded {character}: {relative}")

    metadata = {
        "dataset": "NCCU Cursive Chinese Calligraphy Dataset",
        "repository": f"https://github.com/{REPO}",
        "license": "MIT",
        "license_file": "LICENSE",
        "attribution": "VIPLab, National Chengchi University; images reorganized with permission from shufa.supfree.net.",
        "split": args.split,
        "items": downloaded,
    }
    (output / "metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"downloaded {len(downloaded)} images to {output}")


if __name__ == "__main__":
    main()
