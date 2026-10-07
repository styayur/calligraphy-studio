from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import Database, db
from app.models import Calligrapher, Dynasty, Glyph, GlyphSource, Style
from app.providers.base import DatasetProvider, RawGlyphRecord
from app.schemas import ImportResult
from app.services.asset_store import AssetStore
from app.utils.paths import slugify
from app.domain import CharacterIdentity, GlyphVariant, ScriptMetadata, RightsRecord, glyph_identity_key
import json


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
        key = (record.dataset, record.work, record.license, record.source_uri, json.dumps(record.rights, sort_keys=True))
        source = cache.get(key)
        if source is not None:
            return source
        statement = select(GlyphSource).where(GlyphSource.dataset == record.dataset)
        if record.work is None:
            statement = statement.where(GlyphSource.work.is_(None))
        else:
            statement = statement.where(GlyphSource.work == record.work)
        candidates = session.scalars(statement).all()
        source = next((row for row in candidates if row.license == record.license and row.source_uri == record.source_uri
                       and RightsRecord.model_validate(row.rights or {}).model_dump() == record.rights), None)
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
            def begin_checkpoint():
                # sqlite3 legacy transaction mode does not BEGIN for SAVEPOINT.
                # Without a physical outer transaction, RELEASE commits each row.
                # Keep this scoped to imports; migration/other session semantics stay stable.
                if self.database.engine.dialect.name == 'sqlite':
                    connection=session.connection()
                    if not connection.connection.dbapi_connection.in_transaction:
                        connection.exec_driver_sql('BEGIN')
            begin_checkpoint()
            for record in provider.iter_records():
                try:
                    identity = CharacterIdentity.model_validate(record.identity or {"text": record.character}).model_dump()
                    if identity["text"] != record.character:
                        raise ValueError("Glyph semantic identity does not match its character")
                    record.rights = RightsRecord.model_validate(record.rights).model_dump()
                    variant = GlyphVariant.model_validate(record.variant).model_dump()
                    culture = ScriptMetadata.model_validate(record.culture).model_dump()
                    for field in ("locale", "language", "script"):
                        if identity.get(field) and culture.get(field) and identity[field] != culture[field]:
                            raise ValueError(f"Conflicting identity/source {field}")
                        identity[field] = identity.get(field) or culture.get(field)
                        culture[field] = culture.get(field) or identity.get(field)
                    identity_key = glyph_identity_key(identity, culture, variant)
                    with session.begin_nested():
                        session.flush()
                        asset = self.asset_store.persist(record)
                        calligrapher = self._calligrapher(session, record.calligrapher, calligraphers)
                        style = self._style(session, record.style, styles)
                        dynasty = self._dynasty(session, record.dynasty, dynasties)
                        source = self._source(session, record, sources)

                        existing = session.scalar(
                            select(Glyph.id).where(
                                Glyph.identity_key == identity_key,
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
                                identity=identity,
                                variant=variant,
                                identity_key=identity_key,
                                language=culture["language"], locale=culture["locale"], script=culture["script"],
                                writing_tradition=culture["writing_tradition"], variant_type=variant["type"],
                                orthography=culture["orthography"], period=culture["period"], region=culture["region"],
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
                                metadata_json={**record.metadata, "source_collection": culture["source_collection"]},
                            )
                        )
                    imported += 1
                    if imported % 100 == 0:
                        session.flush()
                        session.commit()
                        begin_checkpoint()
                except Exception as exc:
                    calligraphers.clear(); styles.clear(); dynasties.clear(); sources.clear()
                    failed += 1
                    if len(errors) < 50:
                        index = record.source_index if record.source_index is not None else "?"
                        errors.append(f"sample {index}: {exc}")
        return ImportResult(imported=imported, skipped=skipped, failed=failed, errors=errors)
