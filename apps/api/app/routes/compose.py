from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.routes.deps import get_session
from app.schemas import BatchComposeRequest, BatchComposeResponse
from app.services.asset_store import AssetStore
from app.services.batch_service import BatchComposeService
from app.services.fallback_service import FallbackService
from app.services.glyph_importer import GlyphImporter
from app.services.glyph_service import GlyphService

router = APIRouter(tags=["composition"])


def _service(request: Request) -> BatchComposeService:
    settings = request.app.state.settings
    glyph_service = GlyphService()
    fallback = FallbackService(
        glyph_service,
        glyph_importer=GlyphImporter(AssetStore(settings.assets_dir), request.app.state.db),
        hanzi_cache_dir=settings.hanzi_data_dir,
        fetch_remote_hanzi=settings.fetch_remote_hanzi,
    )
    return BatchComposeService(glyph_service, fallback)


@router.post("/compose/batch", response_model=BatchComposeResponse)
def compose_batch(
    payload: BatchComposeRequest,
    request: Request,
    session: Session = Depends(get_session),
) -> BatchComposeResponse:
    return _service(request).compose(session, payload)
