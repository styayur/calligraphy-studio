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
        limit=limit,
        offset=offset,
    )


@router.get("/glyph/{glyph_id}", response_model=GlyphRead)
def get_glyph(glyph_id: str, session: Session = Depends(get_session)) -> GlyphRead:
    result = service.get(session, glyph_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Glyph not found")
    return result