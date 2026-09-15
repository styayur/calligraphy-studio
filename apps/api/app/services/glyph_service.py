from __future__ import annotations

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models import Calligrapher, Dynasty, Glyph, GlyphSource, Style
from app.schemas import (
    GlyphAppearanceSchema,
    GlyphAssetSchema,
    GlyphListResponse,
    GlyphProvenanceSchema,
    GlyphRead,
    GlyphSourceSchema,
    GlyphTransformSchema,
)


def glyph_to_schema(glyph: Glyph) -> GlyphRead:
    return GlyphRead(
        id=glyph.id,
        character=glyph.character,
        source=GlyphSourceSchema(
            dataset=glyph.source.dataset,
            calligrapher=glyph.calligrapher.name if glyph.calligrapher else None,
            style=glyph.style.name if glyph.style else None,
            dynasty=glyph.dynasty.name if glyph.dynasty else None,
            work=glyph.source.work,
            license=glyph.source.license,
            license_url=glyph.source.license_url,
            rights=glyph.source.rights or {},
        ),
        asset=GlyphAssetSchema(
            type=glyph.asset_type,
            url=glyph.asset_url,
            width=glyph.width,
            height=glyph.height,
            bbox=glyph.bbox,
        ),
        transform=GlyphTransformSchema(),
        appearance=GlyphAppearanceSchema(),
        provenance=GlyphProvenanceSchema(
            type=glyph.provenance_type,
            confidence=glyph.confidence,
        ),
    )


class GlyphService:
    @staticmethod
    def _query(
        *,
        character: str | None = None,
        q: str | None = None,
        calligrapher: str | None = None,
        style: str | None = None,
        dynasty: str | None = None,
        work: str | None = None,
        dataset: str | None = None,
    ):
        statement = (
            select(Glyph)
            .outerjoin(Calligrapher, Glyph.calligrapher_id == Calligrapher.id)
            .outerjoin(Style, Glyph.style_id == Style.id)
            .outerjoin(Dynasty, Glyph.dynasty_id == Dynasty.id)
            .options(
                selectinload(Glyph.source),
                selectinload(Glyph.calligrapher),
                selectinload(Glyph.style),
                selectinload(Glyph.dynasty),
            )
        )
        if character:
            statement = statement.where(Glyph.character == character)
        if q:
            term = q.strip()
            if len(term) == 1:
                statement = statement.where(Glyph.character == term)
            else:
                statement = statement.where(
                    or_(
                        Glyph.character == term,
                        Glyph.character.like(f"%{term}%"),
                        Calligrapher.name.like(f"%{term}%"),
                        Style.name.like(f"%{term}%"),
                        Dynasty.name.like(f"%{term}%"),
                    )
                )
        if calligrapher:
            statement = statement.where(Calligrapher.name == calligrapher)
        if style:
            statement = statement.where(Style.name == style)
        if dynasty:
            statement = statement.where(Dynasty.name == dynasty)
        if work:
            statement = statement.where(Glyph.source.has(work=work))
        if dataset:
            statement = statement.join(GlyphSource).where(GlyphSource.dataset == dataset)
        return statement

    def list(
        self,
        session: Session,
        *,
        character: str | None = None,
        q: str | None = None,
        calligrapher: str | None = None,
        style: str | None = None,
        dynasty: str | None = None,
        work: str | None = None,
        dataset: str | None = None,
        limit: int = 60,
        offset: int = 0,
    ) -> GlyphListResponse:
        statement = self._query(
            character=character,
            q=q,
            calligrapher=calligrapher,
            style=style,
            dynasty=dynasty,
            work=work,
            dataset=dataset,
        )
        total = session.scalar(select(func.count()).select_from(statement.subquery())) or 0
        rows = session.scalars(
            statement.order_by(Glyph.created_at.desc(), Glyph.id).limit(limit).offset(offset)
        ).all()
        return GlyphListResponse(
            items=[glyph_to_schema(row) for row in rows],
            total=total,
            limit=limit,
            offset=offset,
        )

    def get(self, session: Session, glyph_id: str) -> GlyphRead | None:
        statement = (
            select(Glyph)
            .options(
                selectinload(Glyph.source),
                selectinload(Glyph.calligrapher),
                selectinload(Glyph.style),
                selectinload(Glyph.dynasty),
            )
            .where(Glyph.id == glyph_id)
        )
        row = session.scalar(statement)
        return glyph_to_schema(row) if row else None