from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import Database, db
from app.models import Calligrapher, Dynasty, Glyph, GlyphSource, Style
from app.providers.base import DatasetProvider, RawGlyphRecord
from app.schemas import ImportResult
from app.services.asset_store import AssetStore
from app.utils.paths import slugify


class GlyphImporter:
    def __init__(self, asset_store: AssetStore, database: Database | None = None) -> None:
        self.asset_store = asset_store
        self.database = database or db

    @staticmethod
    def _calligrapher(session: Session, name: str | None, cache: dict[str, Calligrapher]):
        if not name:
            return None
        if name not in cache:
            row = session.scalar(select(Calligrapher).where(Calligrapher.name == name))
            if row is None:
                row = Calligrapher(name=name, slug=slugify(name, "calligrapher"))
                session.add(row)
                session.flush()
            cache[name] = row
        return cache[name]

    @staticmethod
    def _style(session: Session, name: str | None, cache: dict[str, Style]):
        if not name:
            return None
        if name not in cache:
            row = session.scalar(select(Style).where(Style.name == name))
            if row is None:
                row = Style(name=name, slug=slugify(name, "style"))
                session.add(row)
                session.flush()
            cache[name] = row
        return cache[name]

    @staticmethod
    def _dynasty(session: Session, name: str | None, cache: dict[str, Dynasty]):
        if not name:
            return None
        if name not in cache:
            row = session.scalar(select(Dynasty).where(Dynasty.name == name))
            if row is None:
                row = Dynasty(name=name, slug=slugify(name, "dynasty"))
                session.add(row)
                session.flush()
            cache[name] = row
        return cache[name]

    @staticmethod
    def _source(session: Session, record: RawGlyphRecord, cache: dict[tuple, GlyphSource]):
        key = (record.dataset, record.work)
        source = cache.get(key)
        if source is not None:
            return source
        statement = select(GlyphSource).where(GlyphSource.dataset == record.dataset)
        if record.work is None:
            statement = statement.where(GlyphSource.work.is_(None))
        else:
            statement = statement.where(GlyphSource.work == record.work)
        source = session.scalar(statement)
        if source is None:
            source = GlyphSource(
                dataset=record.dataset,
                work=record.work,
                license=record.license,
                license_url=record.license_url,
                source_uri=record.source_uri,
                rights=record.rights,
            )
            session.add(source)
            session.flush()
        cache[key] = source
        return source

    def import_provider(self, provider: DatasetProvider) -> ImportResult:
        imported = skipped = failed = 0
        errors: list[str] = []
        calligraphers: dict[str, Calligrapher] = {}
        styles: dict[str, Style] = {}
        dynasties: dict[str, Dynasty] = {}
        sources: dict[tuple, GlyphSource] = {}

        with self.database.session() as session:
            for record in provider.iter_records():
                try:
                    asset = self.asset_store.persist(record)
                    calligrapher = self._calligrapher(session, record.calligrapher, calligraphers)
                    style = self._style(session, record.style, styles)
                    dynasty = self._dynasty(session, record.dynasty, dynasties)
                    source = self._source(session, record, sources)

                    existing = session.scalar(
                        select(Glyph.id).where(
                            Glyph.character == record.character,
                            Glyph.source_id == source.id,
                            Glyph.checksum == asset.checksum,
                        )
                    )
                    if existing:
                        skipped += 1
                        continue

                    session.add(
                        Glyph(
                            character=record.character,
                            calligrapher=calligrapher,
                            style=style,
                            dynasty=dynasty,
                            source=source,
                            asset_url=asset.url,
                            asset_type=asset.asset_type,
                            width=asset.width,
                            height=asset.height,
                            bbox=asset.bbox,
                            checksum=asset.checksum,
                            original_filename=asset.original_filename,
                            provenance_type=record.provenance_type,
                            confidence=record.confidence,
                            metadata_json=record.metadata,
                        )
                    )
                    imported += 1
                    if imported % 1000 == 0:
                        session.flush()
                except Exception as exc:
                    failed += 1
                    if len(errors) < 50:
                        index = record.source_index if record.source_index is not None else "?"
                        errors.append(f"sample {index}: {exc}")
        return ImportResult(imported=imported, skipped=skipped, failed=failed, errors=errors)