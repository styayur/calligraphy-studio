from __future__ import annotations

import json
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = "https://raw.githubusercontent.com/google/fonts/main/ofl"
FONTS = [
    ("mashanzheng", "MaShanZheng-Regular.ttf", "OFL-ma-shan-zheng.txt"),
    ("zhimangxing", "ZhiMangXing-Regular.ttf", "OFL-zhi-mang-xing.txt"),
    ("liujianmaocao", "LiuJianMaoCao-Regular.ttf", "OFL-liu-jian-mao-cao.txt"),
]


def fetch(url: str, destination: Path) -> None:
    request = Request(url, headers={"User-Agent": "CalligraphyStudio/0.3"})
    with urlopen(request, timeout=60) as response:  # noqa: S310
        data = response.read()
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(data)
    print(f"wrote {destination}")


def main() -> None:
    output = Path(__file__).resolve().parents[1] / "samples" / "fonts"
    for directory, filename, license_name in FONTS:
        fetch(f"{ROOT}/{directory}/{filename}", output / "ofl" / directory / filename)
        fetch(f"{ROOT}/{directory}/OFL.txt", output / "licenses" / license_name)
    metadata = {
        "source": "Google Fonts",
        "license": "SIL Open Font License 1.1",
        "fonts": [filename for _, filename, _ in FONTS],
    }
    (output / "metadata.json").write_text(
        json.dumps(metadata, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
