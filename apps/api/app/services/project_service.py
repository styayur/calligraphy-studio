from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Project
from app.schemas import ProjectCreate, ProjectUpdate


class ProjectService:
    def list(self, session: Session) -> list[Project]:
        return list(session.scalars(select(Project).order_by(Project.updated_at.desc())).all())

    def get(self, session: Session, project_id: str) -> Project | None:
        return session.get(Project, project_id)

    def create(self, session: Session, payload: ProjectCreate) -> Project:
        project = Project(name=payload.name, document=payload.document.model_dump(mode="json"))
        session.add(project)
        session.flush()
        return project

    def update(self, session: Session, project: Project, payload: ProjectUpdate) -> Project:
        if payload.name is not None:
            project.name = payload.name
        if payload.document is not None:
            project.document = payload.document.model_dump(mode="json")
        session.flush()
        return project

    def delete(self, session: Session, project: Project) -> None:
        session.delete(project)