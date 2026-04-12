from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.core.deps import get_current_user, require_role
from app.schemas.catalogs import SubcategoryCreate, SubcategoryUpdate, SubcategoryResponse
from app.services.catalog_service import SubcategoryService

router = APIRouter(prefix="/subcategories", tags=["Catálogos — Subcategorías"])

@router.get("", response_model=List[SubcategoryResponse])
def list_subcategories(category_id: int = Query(...), active_only: bool = True, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return [SubcategoryResponse.model_validate(s) for s in SubcategoryService.list_subcategories(db, category_id, active_only)]

@router.post("", response_model=SubcategoryResponse, status_code=201)
def create_subcategory(data: SubcategoryCreate, db: Session = Depends(get_db), current_user=Depends(require_role("admin"))):
    return SubcategoryResponse.model_validate(SubcategoryService.create_subcategory(db, data, current_user.id))

@router.put("/{subcategory_id}", response_model=SubcategoryResponse)
def update_subcategory(subcategory_id: int, data: SubcategoryUpdate, db: Session = Depends(get_db), current_user=Depends(require_role("admin"))):
    return SubcategoryResponse.model_validate(SubcategoryService.update_subcategory(db, subcategory_id, data, current_user.id))

from app.services.catalog_service import CategoryDeleteService

@router.delete("/{subcategory_id}", status_code=200)
def delete_subcategory(subcategory_id: int, db: Session = Depends(get_db), current_user=Depends(require_role("admin"))):
    CategoryDeleteService.delete_subcategory(db, subcategory_id, current_user.id)
    return {"detail": "Subcategoría eliminada"}
