from __future__ import annotations

from pathlib import Path

from sqlalchemy import func, select

from app.config import Settings
from app.database import Database
from app.models import Glyph
from app.providers.font_manifest import FontManifestProvider
from app.providers.mccd import MCCDManifestProvider
from app.providers.nccu_cursive import NCCUCursiveProvider
from app.services.asset_store import AssetStore
from app.services.glyph_importer import GlyphImporter


def seed_demo_if_empty(database: Database, settings: Settings) -> int:
    manifest: Path = settings.demo_manifest
    if not settings.seed_demo or not manifest.is_file():
        return 0

    with database.session() as session:
        existing = session.scalar(select(func.count()).select_from(Glyph)) or 0
    if existing:
        return 0

    provider = MCCDManifestProvider(
        manifest_path=manifest,
        dataset_name="Demo",
        license_name="CC0-1.0",
        license_url="https://creativecommons.org/publicdomain/zero/1.0/",
        rights={
            "commercial_use": True,
            "derivatives_allowed": True,
            "redistribution_allowed": True,
            "research_use": True,
        },
    )
    result = GlyphImporter(AssetStore(settings.assets_dir), database).import_provider(provider)
    return result.imported

def seed_cursive_if_missing(database: Database, settings: Settings) -> int:
    if not settings.seed_cursive or not settings.cursive_sample_root.is_dir():
        return 0

    with database.session() as session:
        existing = session.scalar(
            select(func.count())
            .select_from(Glyph)
            .where(Glyph.style.has(name="草书"))
        ) or 0
    if existing:
        return 0

    provider = NCCUCursiveProvider(
        dataset_root=settings.cursive_sample_root,
        split="Test",
        limit_per_character=3,
        include_augmented=False,
    )
    result = GlyphImporter(AssetStore(settings.assets_dir), database).import_provider(provider)
    return result.imported


def seed_fonts_if_missing(database: Database, settings: Settings) -> int:
    manifest = settings.font_manifest
    if not settings.seed_fonts or not manifest.is_file():
        return 0

    with database.session() as session:
        existing = session.scalar(
            select(func.count())
            .select_from(Glyph)
            .where(Glyph.source.has(dataset="OFL Calligraphy Fonts"))
        ) or 0
    if existing:
        return 0

    provider = FontManifestProvider(
        manifest_path=manifest,
        include_noncommercial=settings.include_noncommercial_fonts,
    )
    result = GlyphImporter(AssetStore(settings.assets_dir), database).import_provider(provider)
    return result.imported
