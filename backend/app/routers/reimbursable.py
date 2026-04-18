"""Router: gastos reembolsables."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.deps import get_current_user, require_role
from app.schemas.financial_modules import ReimbursableCreate, ReimbursableReimburse, ReimbursableOut
from app.services import reimbursable_service

router = APIRouter(prefix="/reimbursable-expenses", tags=["reimbursable"])


@router.get("", response_model=list[ReimbursableOut])
async def list_all(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    user = Depends(require_role("admin", "contable", "consulta")),
):
    return reimbursable_service.list_all(db, status=status)


@router.post("", response_model=ReimbursableOut)
async def create(
    data: ReimbursableCreate,
    db: Session = Depends(get_db),
    user = Depends(require_role("admin", "contable")),
):
    return reimbursable_service.create(db, data, user.id)


@router.put("/{item_id}/reimburse", response_model=ReimbursableOut)
async def reimburse(
    item_id: int,
    data: ReimbursableReimburse,
    db: Session = Depends(get_db),
    user = Depends(require_role("gestor", "admin")),
):
    # Deducir delegación: si el usuario es Ambas, tomar la de su sesión abierta
    if user.delegacion in ("Bata", "Malabo"):
        deleg = user.delegacion
    else:
        from app.models import catalogs as _m
        sess = (db.query(_m.CashSession)
                .filter(_m.CashSession.user_id == user.id, _m.CashSession.status == "open")
                .first())
        if not sess:
            raise HTTPException(status_code=400, detail="Debes tener una sesión de caja abierta para esta operación")
        deleg = sess.delegacion
    return reimbursable_service.reimburse(db, item_id, data, user, deleg)