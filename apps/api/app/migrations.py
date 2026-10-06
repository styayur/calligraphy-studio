"""Explicit, repeatable v1 -> v2 migration. Keeps glyph IDs and project payloads.

SQLite rebuilds only glyphs to change its uniqueness boundary. Foreign-key checks
run before commit. Other SQL dialects use ALTER TABLE and a named constraint.
"""
from __future__ import annotations

import json
from sqlalchemy import MetaData, inspect, text
from sqlalchemy.schema import CreateTable

from app.domain import SCHEMA_VERSION, codepoints, glyph_identity_key, unicode_script


def migrate(engine) -> None:
    from app.models import Glyph
    with engine.connect() as connection:
        tables = inspect(connection).get_table_names()
        if "schema_version" in tables:
            version = connection.execute(text("SELECT version FROM schema_version")).scalar()
            if version and version > SCHEMA_VERSION:
                raise ValueError("Database schema is newer than this application")
        if "glyphs" not in tables:
            return
        columns = {c["name"] for c in inspect(connection).get_columns("glyphs")}
        if "identity_key" in columns:
            return
        sqlite = engine.dialect.name == "sqlite"
        if sqlite:
            connection.exec_driver_sql("PRAGMA foreign_keys=OFF")
            connection.commit()
        try:
            with connection.begin():
                additions = {"identity": "JSON", "variant": "JSON", "identity_key": "VARCHAR(500)",
                             "language": "VARCHAR(32)", "locale": "VARCHAR(64)", "script": "VARCHAR(64)",
                             "writing_tradition": "VARCHAR(64)", "variant_type": "VARCHAR(64)",
                             "orthography": "VARCHAR(64)", "period": "VARCHAR(120)", "region": "VARCHAR(120)"}
                for name, sql_type in additions.items():
                    connection.exec_driver_sql(f'ALTER TABLE glyphs ADD COLUMN "{name}" {sql_type}')
                known_chinese_sources = {'NCCU Cursive Chinese Calligraphy Dataset','OFL Calligraphy Fonts','MCCD','Hanzi Writer Structural Data'}
                for row in connection.execute(text("SELECT g.id, g.character, s.dataset FROM glyphs g JOIN glyph_sources s ON g.source_id=s.id")).mappings().all():
                    # Provider-level facts of pre-existing Chinese packs, never a guess from Han text.
                    culture = {'writing_tradition':'Chinese','language':'zh','script':unicode_script(row['character'])} if row['dataset'] in known_chinese_sources else {}
                    identity = {'text':row['character'],'codepoints':codepoints(row['character']), **{k:v for k,v in culture.items() if k != 'writing_tradition'}}
                    connection.execute(text('UPDATE glyphs SET identity=:identity, variant=:variant, identity_key=:key, language=:language, script=:script, writing_tradition=:tradition WHERE id=:id'),
                                       {'id':row['id'],'identity':json.dumps(identity),'variant':'{}','key':glyph_identity_key(identity,culture,{}),
                                        'language':culture.get('language'),'script':culture.get('script'),'tradition':culture.get('writing_tradition')})
                if sqlite:
                    replacement = Glyph.__table__.to_metadata(MetaData(), name="glyphs_v2")
                    # Foreign references resolve against the existing database, not this temporary metadata.
                    from app.database import Base
                    for table in Base.metadata.sorted_tables:
                        if table.name != "glyphs":
                            table.to_metadata(replacement.metadata)
                    connection.execute(CreateTable(replacement))
                    names = ", ".join(f'"{c.name}"' for c in Glyph.__table__.columns)
                    connection.exec_driver_sql(f"INSERT INTO glyphs_v2 ({names}) SELECT {names} FROM glyphs")
                    connection.exec_driver_sql("DROP TABLE glyphs")
                    connection.exec_driver_sql("ALTER TABLE glyphs_v2 RENAME TO glyphs")
                    for index in Glyph.__table__.indexes:
                        index.create(connection)
                    if connection.exec_driver_sql("PRAGMA foreign_key_check").fetchall():
                        raise ValueError("Foreign-key validation failed during glyph migration")
                else:
                    connection.exec_driver_sql("ALTER TABLE glyphs ALTER COLUMN character TYPE VARCHAR(128)")
                    connection.exec_driver_sql("ALTER TABLE glyphs DROP CONSTRAINT uq_glyph_identity")
                    connection.exec_driver_sql("ALTER TABLE glyphs ADD CONSTRAINT uq_glyph_identity UNIQUE (identity_key, source_id, checksum)")
                    for index in Glyph.__table__.indexes:
                        if any(c.name in additions for c in index.columns):
                            index.create(connection)
        finally:
            if sqlite:
                connection.exec_driver_sql("PRAGMA foreign_keys=ON")
                connection.commit()


def record_version(engine) -> None:
    with engine.begin() as connection:
        connection.exec_driver_sql("CREATE TABLE IF NOT EXISTS schema_version (version INTEGER NOT NULL)")
        connection.exec_driver_sql("DELETE FROM schema_version")
        connection.execute(text("INSERT INTO schema_version (version) VALUES (:version)"), {"version": SCHEMA_VERSION})
