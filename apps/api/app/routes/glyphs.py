from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.routes.deps import get_session
from app.schemas import GlyphListResponse, GlyphRead
from app.services.glyph_service import GlyphService

router = APIRouter(tags=["glyphs"])
service = GlyphService()


@router.get("/glyph", response_model=GlyphListResponse)
def query_glyphs(
    character: str | None = None,
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
    mode: str = Query(default="strict", pattern="^(strict|related|cross-tradition)$"),
    designer: str | None = None,
    limit: int = Query(default=60, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_session),
) -> GlyphListResponse:
    return service.list(
        session,
        character=character,
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
        limit=limit,
        offset=offset,
    )


@router.get("/glyphs", response_model=GlyphListResponse)
def list_glyphs(
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
    mode: str = Query(default="strict", pattern="^(strict|related|cross-tradition)$"),
    designer: str | None = None,
    limit: int = Query(default=60, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_session),
) -> GlyphListResponse:
    return service.list(
        session,
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
        limit=limit,
        offset=offset,
    )


@router.get("/glyph/{glyph_id}", response_model=GlyphRead)
def get_glyph(glyph_id: str, session: Session = Depends(get_session)) -> GlyphRead:
    result = service.get(session, glyph_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Glyph not found")
    return result