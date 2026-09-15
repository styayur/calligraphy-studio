from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.routes.deps import get_session
from app.schemas import EmbeddingIndexResult, SimilarityResponse
from app.services.embedding_service import EmbeddingService

router = APIRouter(tags=["similarity"])


def _service(request: Request) -> EmbeddingService:
    return EmbeddingService(request.app.state.settings.assets_dir)


@router.post("/similarity/reindex", response_model=EmbeddingIndexResult)
def reindex(
    request: Request,
    characters: str | None = Query(default=None, description="Comma-separated character filter"),
    limit: int | None = Query(default=None, ge=1, le=100000),
    force: bool = False,
    session: Session = Depends(get_session),
) -> EmbeddingIndexResult:
    character_set = {item for item in characters if not item.isspace()} if characters else None
    return _service(request).index(
        session,
        characters=character_set,
        limit=limit,
        force=force,
    )


@router.get("/similarity/{glyph_id}", response_model=SimilarityResponse)
def similar_glyphs(
    glyph_id: str,
    request: Request,
    limit: int = Query(default=20, ge=1, le=100),
    same_style: bool = True,
    same_dataset: bool = False,
    session: Session = Depends(get_session),
) -> SimilarityResponse:
    try:
        return _service(request).similar(
            session,
            glyph_id=glyph_id,
            limit=limit,
            same_style=same_style,
            same_dataset=same_dataset,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
