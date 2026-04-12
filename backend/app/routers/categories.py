from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.core.deps import get_current_user, require_role
from app.schemas.catalogs import CategoryCreate, CategoryUpdate, CategoryResponse, PaginatedResponse
from app.services.catalog_service import CategoryService

router = APIRouter(prefix="/categories", tags=["Catálogos — Categorías"])

@router.get("", response_model=PaginatedResponse)
def list_categories(type: Optional[str] = None, active_only: bool = True, page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=200), db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    items, total = CategoryService.list_categories(db, type_filter=type, active_only=active_only, page=page, page_size=page_size)
    return {"items": [CategoryResponse.model_validate(c) for c in items], "total": total, "page": page, "page_size": page_size, "pages": (total + page_size - 1) // page_size}

@router.post("", response_model=CategoryResponse, status_code=201)
def create_category(data: CategoryCreate, db: Session = Depends(get_db), current_user=Depends(require_role("admin"))):
    return CategoryResponse.model_validate(CategoryService.create_category(db, data, current_user.id))

@router.put("/{category_id}", response_model=CategoryResponse)
def update_category(category_id: int, data: CategoryUpdate, db: Session = Depends(get_db), current_user=Depends(require_role("admin"))):
    return CategoryResponse.model_validate(CategoryService.update_category(db, category_id, data, current_user.id))

from app.services.catalog_service import CategoryDeleteService

@router.delete("/{category_id}", status_code=200)
def delete_category(category_id: int, db: Session = Depends(get_db), current_user=Depends(require_role("admin"))):
    CategoryDeleteService.delete_category(db, category_id, current_user.id)
    return {"detail": "Categoría eliminada"}
