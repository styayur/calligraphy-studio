from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.providers.font_manifest import FontManifestProvider
from app.providers.mccd import MCCDManifestProvider
from app.providers.nccu_cursive import NCCUCursiveProvider
from app.services.asset_store import AssetStore
from app.services.glyph_importer import GlyphImporter

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEMO_MANIFEST = PROJECT_ROOT / "samples" / "demo" / "manifest.csv"
CURSIVE_ROOT = PROJECT_ROOT / "samples" / "cursive" / "raw"
FONT_MANIFEST = PROJECT_ROOT / "samples" / "fonts" / "manifest.json"
DEMO_RIGHTS = {
    "commercial_use": True,
    "derivatives_allowed": True,
    "redistribution_allowed": True,
    "research_use": True,
}


@pytest.fixture(scope="module")
def client(tmp_path_factory: pytest.TempPathFactory) -> Iterator[TestClient]:
    tmp_path = tmp_path_factory.mktemp("calligraphy-api")
    database_path = (tmp_path / "test.db").as_posix()
    settings = Settings(
        database_url=f"sqlite:///{database_path}",
        assets_dir=tmp_path / "assets",
        hanzi_data_dir=tmp_path / "hanzi-writer",
        seed_demo=False,
        seed_cursive=False,
        auto_index_embeddings=False,
        fetch_remote_hanzi=False,
    )
    application = create_app(settings)
    with TestClient(application) as test_client:
        importer = GlyphImporter(AssetStore(settings.assets_dir), application.state.db)
        importer.import_provider(
            MCCDManifestProvider(
                manifest_path=DEMO_MANIFEST,
                dataset_name="Demo",
                license_name="CC0-1.0",
                license_url="https://creativecommons.org/publicdomain/zero/1.0/",
                rights=DEMO_RIGHTS,
            )
        )
        importer.import_provider(
            NCCUCursiveProvider(
                dataset_root=CURSIVE_ROOT,
                split="Test",
                limit_per_character=2,
                include_augmented=False,
            )
        )
        importer.import_provider(
            FontManifestProvider(
                FONT_MANIFEST,
                characters={"山"},
            )
        )
        yield test_client
