from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.routes.deps import get_session
from app.services.asset_store import AssetStore
from app.services.fallback_service import FallbackRequest, FallbackResult, FallbackService
from app.services.glyph_importer import GlyphImporter
from app.services.glyph_service import GlyphService

router = APIRouter(tags=["fallback"])


def _service(request: Request) -> FallbackService:
    settings = request.app.state.settings
    return FallbackService(
        GlyphService(),
        glyph_importer=GlyphImporter(AssetStore(settings.assets_dir), request.app.state.db),
        hanzi_cache_dir=settings.hanzi_data_dir,
        fetch_remote_hanzi=settings.fetch_remote_hanzi,
    )


@router.post("/fallback/resolve", response_model=FallbackResult)
def resolve_fallback(
    request: FallbackRequest,
    http_request: Request,
    session: Session = Depends(get_session),
) -> FallbackResult:
    return _service(http_request).resolve(session, request)
