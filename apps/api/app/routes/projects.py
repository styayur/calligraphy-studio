from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.routes.deps import get_session
from app.schemas import ProjectCreate, ProjectListItem, ProjectRead, ProjectUpdate
from app.services.project_service import ProjectService

router = APIRouter(prefix="/projects", tags=["projects"])
service = ProjectService()


@router.get("", response_model=list[ProjectListItem])
def list_projects(session: Session = Depends(get_session)) -> list[ProjectListItem]:
    return [ProjectListItem(id=row.id, name=row.name) for row in service.list(session)]


@router.post("", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
def create_project(
    payload: ProjectCreate, session: Session = Depends(get_session)
) -> ProjectRead:
    row = service.create(session, payload)
    return ProjectRead(id=row.id, name=row.name, document=row.document)


@router.get("/{project_id}", response_model=ProjectRead)
def get_project(project_id: str, session: Session = Depends(get_session)) -> ProjectRead:
    row = service.get(session, project_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return ProjectRead(id=row.id, name=row.name, document=row.document)


@router.put("/{project_id}", response_model=ProjectRead)
def update_project(
    project_id: str,
    payload: ProjectUpdate,
    session: Session = Depends(get_session),
) -> ProjectRead:
    row = service.get(session, project_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Project not found")
    row = service.update(session, row, payload)
    return ProjectRead(id=row.id, name=row.name, document=row.document)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: str, session: Session = Depends(get_session)) -> Response:
    row = service.get(session, project_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Project not found")
    service.delete(session, row)
    return Response(status_code=status.HTTP_204_NO_CONTENT)