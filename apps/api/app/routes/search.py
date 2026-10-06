from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.routes.deps import get_session
from app.schemas import GlyphListResponse
from app.services.glyph_service import GlyphService

router = APIRouter(tags=["search"])
service = GlyphService()


@router.get("/search", response_model=GlyphListResponse)
def search(
    q: str | None = Query(default=None, max_length=120),
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
        q=q,
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