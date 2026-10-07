from __future__ import annotations

from sqlalchemy import select, or_
from sqlalchemy.orm import Session

from app.models import Calligrapher, Dynasty, GlyphSource, Style, Glyph
from app.schemas import MetadataItem, MetadataResponse


class MetadataService:
    def list(self, session: Session, writing_tradition: str = "Chinese") -> MetadataResponse:
        # Preserve the v1 Chinese metadata default; '*' explicitly requests every tradition.
        culture = or_(Glyph.writing_tradition == writing_tradition, Glyph.writing_tradition.is_(None)) if writing_tradition == "Chinese" else Glyph.writing_tradition == writing_tradition
        calligraphers_query = select(Calligrapher)
        styles_query = select(Style)
        if writing_tradition != "*":
            calligraphers_query = calligraphers_query.where(select(Glyph.id).where(Glyph.calligrapher_id == Calligrapher.id, culture).exists())
            styles_query = styles_query.where(select(Glyph.id).where(Glyph.style_id == Style.id, culture).exists())
        calligraphers = session.scalars(calligraphers_query.order_by(Calligrapher.name)).all()
        styles = session.scalars(styles_query.order_by(Style.name)).all()
        dynasties = session.scalars(
            select(Dynasty).order_by(Dynasty.sort_order, Dynasty.name)
        ).all()
        datasets_query = select(GlyphSource.dataset).distinct()
        if writing_tradition != "*":
            datasets_query = datasets_query.where(select(Glyph.id).where(Glyph.source_id == GlyphSource.id, culture).exists())
        datasets = session.scalars(datasets_query.order_by(GlyphSource.dataset)).all()
        return MetadataResponse(
            calligraphers=[MetadataItem(id=row.id, name=row.name) for row in calligraphers],
            styles=[MetadataItem(id=row.id, name=row.name) for row in styles],
            dynasties=[MetadataItem(id=row.id, name=row.name) for row in dynasties],
            datasets=list(datasets),
        )
