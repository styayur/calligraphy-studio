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
        identity=glyph.identity or None,
        variant=glyph.variant or {},
        metadata=glyph.metadata_json or {},
        source=GlyphSourceSchema(
            dataset=glyph.source.dataset,
            calligrapher=glyph.calligrapher.name if glyph.calligrapher else None,
            style=glyph.style.name if glyph.style else None,
            dynasty=glyph.dynasty.name if glyph.dynasty else None,
            work=glyph.source.work,
            license=glyph.source.license,
            license_url=glyph.source.license_url,
            rights=glyph.source.rights or {},
            language=glyph.language, locale=glyph.locale, script=glyph.script,
            writing_tradition=glyph.writing_tradition, orthography=glyph.orthography,
            period=glyph.period, region=glyph.region,
            source_uri=(glyph.metadata_json or {}).get("source_uri") or glyph.source.source_uri,
            **{key: (glyph.metadata_json or {}).get(key) for key in ["attribution", "designer", "dataset_version", "source_checksum", "license_text", "source_collection"]},
        ),
        asset=GlyphAssetSchema(
            type=glyph.asset_type,
            url=glyph.asset_url,
            width=glyph.width,
            height=glyph.height,
            bbox=glyph.bbox,
            checksum=glyph.checksum,
            processing=(glyph.metadata_json or {}).get("processing"),
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
        language: str | None = None,
        locale: str | None = None,
        script: str | None = None,
        writing_tradition: str | None = None,
        variant_type: str | None = None,
        orthography: str | None = None,
        period: str | None = None,
        region: str | None = None,
        provenance_type: str | None = None,
        commercial_only: bool = False,
        mode: str = "strict",
        designer: str | None = None,
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
        for name, value in {"language": language, "locale": locale, "script": script, "writing_tradition": writing_tradition, "variant_type": variant_type, "orthography": orthography, "period": period, "region": region, "provenance_type": provenance_type}.items():
            if value:
                if name in {"writing_tradition", "locale", "language"} and mode == "cross-tradition":
                    continue
                if name == "locale" and writing_tradition:
                    statement = statement.where(or_(Glyph.locale == value, Glyph.locale.is_(None)))
                    continue
                statement = statement.where(getattr(Glyph, name) == value)
        if writing_tradition == "Japanese" and mode == "strict" and not variant_type:
            statement = statement.where(or_(Glyph.variant_type.is_(None), Glyph.variant_type != "hentaigana"))
            statement = statement.where(or_(Glyph.orthography.is_(None), Glyph.orthography != 'historical-kana'))
        if commercial_only:
            statement = statement.where(Glyph.source.has(GlyphSource.rights["commercial_use"].as_boolean() == True))
        if designer:
            statement = statement.where(Calligrapher.name == designer)
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
        language: str | None = None,
        locale: str | None = None,
        script: str | None = None,
        writing_tradition: str | None = None,
        variant_type: str | None = None,
        orthography: str | None = None,
        period: str | None = None,
        region: str | None = None,
        provenance_type: str | None = None,
        commercial_only: bool = False,
        mode: str = "strict",
        designer: str | None = None,
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
            language=language,
            locale=locale,
            script=script,
            writing_tradition=writing_tradition,
            variant_type=variant_type,
            orthography=orthography,
            period=period,
            region=region,
            provenance_type=provenance_type,
            commercial_only=commercial_only, mode=mode, designer=designer,
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
