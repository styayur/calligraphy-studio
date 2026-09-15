from __future__ import annotations

import re
from collections.abc import Iterator
from pathlib import Path

from app.providers.base import DatasetProvider, RawGlyphRecord

NCCU_DATASET = "NCCU Cursive Chinese Calligraphy Dataset"
NCCU_WORK = "CursiveChineseCalligraphyDataset"
NCCU_LICENSE = "MIT"
NCCU_LICENSE_URL = "https://github.com/nccuviplab/CursiveChineseCalligraphyDataset/blob/master/LICENSE"
NCCU_SOURCE_URI = "https://github.com/nccuviplab/CursiveChineseCalligraphyDataset"
NCCU_RIGHTS = {
    "commercial_use": True,
    "derivatives_allowed": True,
    "redistribution_allowed": True,
    "research_use": True,
    "attribution_required": True,
}

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def base_character(directory_name: str) -> str:
    return re.sub(r"\d+$", "", directory_name).strip()


class NCCUCursiveProvider(DatasetProvider):
    """MIT-licensed cursive dataset organized as split/character/image.jpg."""

    name = "nccu-cursive"

    def __init__(
        self,
        dataset_root: str | Path,
        split: str = "Test",
        characters: set[str] | None = None,
        limit_per_character: int | None = 3,
        include_augmented: bool = False,
        dataset_name: str = NCCU_DATASET,
    ) -> None:
        root = Path(dataset_root).resolve()
        candidates = [
            root / "Cursive_Chinese_Calligraphy_Dataset" / split,
            root / split,
            root,
        ]
        self.split_root = next((candidate for candidate in candidates if candidate.is_dir()), candidates[0])
        self.characters = characters
        self.limit_per_character = limit_per_character
        self.include_augmented = include_augmented
        self.dataset_name = dataset_name

    def iter_records(self) -> Iterator[RawGlyphRecord]:
        if not self.split_root.is_dir():
            raise FileNotFoundError(f"Cursive dataset split not found: {self.split_root}")

        emitted_by_character: dict[str, int] = {}
        index = 0
        directories = sorted(
            (item for item in self.split_root.iterdir() if item.is_dir()),
            key=lambda item: item.name,
        )
        for directory in directories:
            character = base_character(directory.name)
            if not character or (self.characters is not None and character not in self.characters):
                continue
            limit = self.limit_per_character
            if limit is not None and emitted_by_character.get(character, 0) >= limit:
                continue
            files = sorted(
                file
                for file in directory.iterdir()
                if file.is_file() and file.suffix.lower() in IMAGE_EXTENSIONS
            )
            for file in files:
                if not self.include_augmented and file.name.startswith("gen_"):
                    continue
                if limit is not None and emitted_by_character.get(character, 0) >= limit:
                    break
                index += 1
                emitted_by_character[character] = emitted_by_character.get(character, 0) + 1
                yield RawGlyphRecord(
                    character=character,
                    dataset=self.dataset_name,
                    style="草书",
                    dynasty="历代",
                    work=NCCU_WORK,
                    asset_path=file,
                    original_filename=file.name,
                    license=NCCU_LICENSE,
                    license_url=NCCU_LICENSE_URL,
                    source_uri=NCCU_SOURCE_URI,
                    rights=dict(NCCU_RIGHTS),
                    provenance_type="original",
                    metadata={
                        "split": self.split_root.name,
                        "directory_label": directory.name,
                        "augmented": file.name.startswith("gen_"),
                        "acknowledgement": "Images reorganized with permission from shufa.supfree.net.",
                    },
                    source_index=index,
                )
