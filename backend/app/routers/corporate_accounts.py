from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from app.database import get_db
from app.core.deps import get_current_user, require_role
from app.schemas.catalogs import CorporateAccountCreate, CorporateAccountUpdate, CorporateAccountResponse
from app.services.catalog_service import CorporateAccountService

router = APIRouter(prefix="/corporate-accounts", tags=["Catálogos — Cuentas Corporativas"])

@router.get("", response_model=List[CorporateAccountResponse])
def list_accounts(delegacion: Optional[str] = None, active_only: bool = True, db: Session = Depends(get_db), current_user=Depends(require_role("admin", "contable"))):
    return [CorporateAccountResponse.model_validate(a) for a in CorporateAccountService.list_accounts(db, delegacion, active_only)]

@router.post("", response_model=CorporateAccountResponse, status_code=201)
def create_account(data: CorporateAccountCreate, db: Session = Depends(get_db), current_user=Depends(require_role("admin"))):
    return CorporateAccountResponse.model_validate(CorporateAccountService.create_account(db, data, current_user.id))

@router.put("/{account_id}", response_model=CorporateAccountResponse)
def update_account(account_id: int, data: CorporateAccountUpdate, db: Session = Depends(get_db), current_user=Depends(require_role("admin"))):
    return CorporateAccountResponse.model_validate(CorporateAccountService.update_account(db, account_id, data, current_user.id))


@router.delete("/{account_id}")
def delete_account(account_id: int, db: Session = Depends(get_db), current_user=Depends(require_role("admin"))):
    from app.services.catalog_service import CorporateAccountDeleteService
    return CorporateAccountDeleteService.delete_account(db, account_id, current_user.id)
