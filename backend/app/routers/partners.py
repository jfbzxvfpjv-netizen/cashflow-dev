from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.core.deps import get_current_user, require_role
from app.schemas.catalogs import PartnerCreate, PartnerUpdate, PartnerResponse
from app.services.catalog_service import PartnerService

router = APIRouter(prefix="/partners", tags=["Catálogos — Socios"])

def _filter_balance(p, user):
    r = PartnerResponse.model_validate(p)
    if user.role not in ("admin", "contable"):
        r.current_balance = None
    return r

@router.get("", response_model=List[PartnerResponse])
def list_partners(active_only: bool = True, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return [_filter_balance(p, current_user) for p in PartnerService.list_partners(db, active_only)]

@router.post("", response_model=PartnerResponse, status_code=201)
def create_partner(data: PartnerCreate, db: Session = Depends(get_db), current_user=Depends(require_role("admin"))):
    return PartnerResponse.model_validate(PartnerService.create_partner(db, data, current_user.id))

@router.put("/{partner_id}", response_model=PartnerResponse)
def update_partner(partner_id: int, data: PartnerUpdate, db: Session = Depends(get_db), current_user=Depends(require_role("admin"))):
    return PartnerResponse.model_validate(PartnerService.update_partner(db, partner_id, data, current_user.id))
