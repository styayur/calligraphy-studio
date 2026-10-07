"""Re-fetch exact upstream Yuji/Klee binaries; subset reproduction is separate."""
from pathlib import Path
import hashlib
import json
from urllib.request import urlopen, Request

ROOT = Path(__file__).resolve().parents[1]


def main():
    manifest = json.loads((ROOT / "samples/fonts/japanese/manifest.json").read_text(encoding="utf-8"))
    for entry in manifest["fonts"]:
        if not entry.get("download_url"):
            if entry.get("source_role") != "coverage-fallback":
                raise ValueError(f"Missing upstream download URL: {entry['id']}")
            continue  # scripts/build_japanese_coverage.py --fetch reproduces this derivative.
        request = Request(entry["download_url"], headers={"User-Agent": "CalligraphyStudio/0.7"})
        with urlopen(request, timeout=60) as response:
            if response.url != entry["download_url"] or not response.url.startswith((
                "https://raw.githubusercontent.com/Kinutafontfactory/Yuji/",
                "https://raw.githubusercontent.com/fontworks-fonts/Klee/",
            )):
                raise ValueError("Unexpected font download redirect")
            data = response.read(40 * 1024 * 1024 + 1)
        if hashlib.sha256(data).hexdigest() != entry["sha256"]:
            raise ValueError(f"Checksum mismatch: {entry['id']}")
        destination = (ROOT / "samples/fonts/japanese" / entry["path"]).resolve()
        if not destination.is_relative_to(ROOT / "samples/fonts/japanese"):
            raise ValueError("Unsafe destination")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
        print(entry["id"], len(data), entry["sha256"])


if __name__ == "__main__":
    main()
