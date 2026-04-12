from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.core.deps import get_current_user, require_role
from app.schemas.catalogs import VehicleCreate, VehicleUpdate, VehicleResponse, PaginatedResponse
from app.services.catalog_service import VehicleService

router = APIRouter(prefix="/vehicles", tags=["Catálogos — Vehículos"])

@router.get("", response_model=PaginatedResponse)
def list_vehicles(delegacion: Optional[str] = None, active_only: bool = True, search: Optional[str] = None, page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=200), db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    items, total = VehicleService.list_vehicles(db, delegacion=delegacion, active_only=active_only, search=search, page=page, page_size=page_size)
    return {"items": [VehicleResponse.model_validate(v) for v in items], "total": total, "page": page, "page_size": page_size, "pages": (total + page_size - 1) // page_size}

@router.post("", response_model=VehicleResponse, status_code=201)
def create_vehicle(data: VehicleCreate, db: Session = Depends(get_db), current_user=Depends(require_role("admin"))):
    return VehicleResponse.model_validate(VehicleService.create_vehicle(db, data, current_user.id))

@router.put("/{vehicle_id}", response_model=VehicleResponse)
def update_vehicle(vehicle_id: int, data: VehicleUpdate, db: Session = Depends(get_db), current_user=Depends(require_role("admin"))):
    return VehicleResponse.model_validate(VehicleService.update_vehicle(db, vehicle_id, data, current_user.id))
