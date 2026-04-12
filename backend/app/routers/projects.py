from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.core.deps import get_current_user, require_role
from app.schemas.catalogs import ProjectCreate, ProjectUpdate, ProjectResponse, PaginatedResponse
from app.services.catalog_service import ProjectService

router = APIRouter(prefix="/projects", tags=["Catálogos — Proyectos"])

@router.get("", response_model=PaginatedResponse)
def list_projects(active_only: bool = True, search: Optional[str] = None, page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=200), db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    items, total = ProjectService.list_projects(db, active_only=active_only, search=search, page=page, page_size=page_size)
    return {"items": [ProjectResponse.model_validate(p) for p in items], "total": total, "page": page, "page_size": page_size, "pages": (total + page_size - 1) // page_size}

@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return ProjectResponse.model_validate(ProjectService.get_project(db, project_id))

@router.post("", response_model=ProjectResponse, status_code=201)
def create_project(data: ProjectCreate, db: Session = Depends(get_db), current_user=Depends(require_role("admin"))):
    return ProjectResponse.model_validate(ProjectService.create_project(db, data, current_user.id))

@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(project_id: int, data: ProjectUpdate, db: Session = Depends(get_db), current_user=Depends(require_role("admin"))):
    return ProjectResponse.model_validate(ProjectService.update_project(db, project_id, data, current_user.id))
