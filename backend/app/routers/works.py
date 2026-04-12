from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.core.deps import get_current_user, require_role
from app.schemas.catalogs import WorkCreate, WorkCreateInline, WorkUpdate, WorkResponse, PaginatedResponse
from app.services.catalog_service import WorkService

router = APIRouter(prefix="/works", tags=["Catálogos — Obras"])

@router.get("", response_model=PaginatedResponse)
def list_works(project_id: Optional[int] = None, active_only: bool = True, search: Optional[str] = None, page: int = Query(1, ge=1), page_size: int = Query(100, ge=1, le=500), db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    items, total = WorkService.list_works(db, project_id=project_id, active_only=active_only, search=search, page=page, page_size=page_size)
    return {"items": [WorkResponse.model_validate(w) for w in items], "total": total, "page": page, "page_size": page_size, "pages": (total + page_size - 1) // page_size}

@router.post("", response_model=WorkResponse, status_code=201)
def create_work(data: WorkCreate, db: Session = Depends(get_db), current_user=Depends(require_role("admin"))):
    return WorkResponse.model_validate(WorkService.create_work(db, data, current_user.id))

@router.post("/inline", response_model=WorkResponse, status_code=201)
def create_work_inline(data: WorkCreateInline, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return WorkResponse.model_validate(WorkService.create_work_inline(db, data.project_id, data.code, data.name, current_user.id))

@router.put("/{work_id}", response_model=WorkResponse)
def update_work(work_id: int, data: WorkUpdate, db: Session = Depends(get_db), current_user=Depends(require_role("admin"))):
    return WorkResponse.model_validate(WorkService.update_work(db, work_id, data, current_user.id))
