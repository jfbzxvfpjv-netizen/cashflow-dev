from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.core.deps import get_current_user, require_role
from app.schemas.catalogs import SupplierCreate, SupplierUpdate, SupplierResponse, PaginatedResponse
from app.services.catalog_service import SupplierService

router = APIRouter(prefix="/suppliers", tags=["Catálogos — Proveedores"])

@router.get("", response_model=PaginatedResponse)
def list_suppliers(supplier_type: Optional[str] = None, active_only: bool = True, search: Optional[str] = None, page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=200), db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    items, total = SupplierService.list_suppliers(db, supplier_type=supplier_type, active_only=active_only, search=search, page=page, page_size=page_size)
    return {"items": [SupplierResponse.model_validate(s) for s in items], "total": total, "page": page, "page_size": page_size, "pages": (total + page_size - 1) // page_size}

@router.post("", response_model=SupplierResponse, status_code=201)
def create_supplier(data: SupplierCreate, db: Session = Depends(get_db), current_user=Depends(require_role("admin"))):
    return SupplierResponse.model_validate(SupplierService.create_supplier(db, data, current_user.id))

@router.put("/{supplier_id}", response_model=SupplierResponse)
def update_supplier(supplier_id: int, data: SupplierUpdate, db: Session = Depends(get_db), current_user=Depends(require_role("admin"))):
    return SupplierResponse.model_validate(SupplierService.update_supplier(db, supplier_id, data, current_user.id))


@router.delete("/{supplier_id}")
def delete_supplier(supplier_id: int, db: Session = Depends(get_db), current_user=Depends(require_role("admin"))):
    from app.services.catalog_service import SupplierDeleteService
    return SupplierDeleteService.delete_supplier(db, supplier_id, current_user.id)
