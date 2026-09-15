from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.routes.deps import get_session
from app.schemas import MetadataResponse
from app.services.metadata_service import MetadataService

router = APIRouter(tags=["metadata"])
service = MetadataService()


@router.get("/calligraphers")
def calligraphers(session: Session = Depends(get_session)):
    return service.list(session).calligraphers


@router.get("/styles")
def styles(session: Session = Depends(get_session)):
    return service.list(session).styles


@router.get("/dynasties")
def dynasties(session: Session = Depends(get_session)):
    return service.list(session).dynasties


@router.get("/meta", response_model=MetadataResponse)
def metadata(session: Session = Depends(get_session)) -> MetadataResponse:
    return service.list(session)