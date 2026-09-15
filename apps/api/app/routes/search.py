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
    q: str = Query(min_length=1, max_length=120),
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
        q=q,
        calligrapher=calligrapher,
        style=style,
        dynasty=dynasty,
        work=work,
        dataset=dataset,
        limit=limit,
        offset=offset,
    )