from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Calligrapher, Dynasty, GlyphSource, Style
from app.schemas import MetadataItem, MetadataResponse


class MetadataService:
    def list(self, session: Session) -> MetadataResponse:
        calligraphers = session.scalars(select(Calligrapher).order_by(Calligrapher.name)).all()
        styles = session.scalars(select(Style).order_by(Style.name)).all()
        dynasties = session.scalars(
            select(Dynasty).order_by(Dynasty.sort_order, Dynasty.name)
        ).all()
        datasets = session.scalars(
            select(GlyphSource.dataset).distinct().order_by(GlyphSource.dataset)
        ).all()
        return MetadataResponse(
            calligraphers=[MetadataItem(id=row.id, name=row.name) for row in calligraphers],
            styles=[MetadataItem(id=row.id, name=row.name) for row in styles],
            dynasties=[MetadataItem(id=row.id, name=row.name) for row in dynasties],
            datasets=list(datasets),
        )