from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Index, Integer, JSON, LargeBinary, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Calligrapher(Base):
    __tablename__ = "calligraphers"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    slug: Mapped[str] = mapped_column(String(160), unique=True, index=True)
    glyphs: Mapped[list[Glyph]] = relationship(back_populates="calligrapher")


class Style(Base):
    __tablename__ = "styles"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    slug: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    glyphs: Mapped[list[Glyph]] = relationship(back_populates="style")


class Dynasty(Base):
    __tablename__ = "dynasties"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    slug: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    glyphs: Mapped[list[Glyph]] = relationship(back_populates="dynasty")


class GlyphSource(Base):
    __tablename__ = "glyph_sources"
    __table_args__ = (
        UniqueConstraint("dataset", "work", name="uq_glyph_source_dataset_work"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    dataset: Mapped[str] = mapped_column(String(120), index=True)
    work: Mapped[str | None] = mapped_column(String(240), nullable=True)
    license: Mapped[str | None] = mapped_column(String(240), nullable=True)
    license_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    source_uri: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    rights: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    glyphs: Mapped[list[Glyph]] = relationship(back_populates="source")


class Glyph(Base):
    __tablename__ = "glyphs"
    __table_args__ = (
        UniqueConstraint("character", "source_id", "checksum", name="uq_glyph_identity"),
        Index("ix_glyphs_character_created", "character", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    character: Mapped[str] = mapped_column(String(16), index=True)
    calligrapher_id: Mapped[int | None] = mapped_column(
        ForeignKey("calligraphers.id"), nullable=True, index=True
    )
    style_id: Mapped[int | None] = mapped_column(ForeignKey("styles.id"), nullable=True, index=True)
    dynasty_id: Mapped[int | None] = mapped_column(
        ForeignKey("dynasties.id"), nullable=True, index=True
    )
    source_id: Mapped[int] = mapped_column(ForeignKey("glyph_sources.id"), index=True)
    asset_url: Mapped[str] = mapped_column(String(1000))
    asset_type: Mapped[str] = mapped_column(String(24))
    width: Mapped[int] = mapped_column(Integer)
    height: Mapped[int] = mapped_column(Integer)
    bbox: Mapped[list[float]] = mapped_column(JSON)
    checksum: Mapped[str] = mapped_column(String(64), index=True)
    original_filename: Mapped[str | None] = mapped_column(String(500), nullable=True)
    provenance_type: Mapped[str] = mapped_column(String(24), default="original")
    confidence: Mapped[float | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    metadata_json: Mapped[dict] = mapped_column("metadata", JSON, default=dict)

    calligrapher: Mapped[Calligrapher | None] = relationship(back_populates="glyphs")
    style: Mapped[Style | None] = relationship(back_populates="glyphs")
    dynasty: Mapped[Dynasty | None] = relationship(back_populates="glyphs")
    source: Mapped[GlyphSource] = relationship(back_populates="glyphs")


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(240), default="Untitled")
    document: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

class GlyphEmbedding(Base):
    __tablename__ = "glyph_embeddings"
    __table_args__ = (
        UniqueConstraint("glyph_id", "model_name", name="uq_glyph_embedding_model"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    glyph_id: Mapped[str] = mapped_column(
        ForeignKey("glyphs.id", ondelete="CASCADE"), index=True
    )
    model_name: Mapped[str] = mapped_column(String(120), index=True)
    dimension: Mapped[int] = mapped_column(Integer)
    vector: Mapped[bytes] = mapped_column(LargeBinary)
    norm: Mapped[float] = mapped_column()
    source_checksum: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
