"""Router: pagos fraccionados."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.deps import get_current_user, require_role
from app.schemas.financial_modules import InstallmentCreate, InstallmentPay, InstallmentOut
from app.services import installments_service

router = APIRouter(prefix="/installments", tags=["installments"])


@router.get("", response_model=list[InstallmentOut])
async def list_installments(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    return installments_service.list_all(db, status=status)


@router.post("", response_model=InstallmentOut)
async def create_installment(
    data: InstallmentCreate,
    db: Session = Depends(get_db),
    user = Depends(require_role("admin", "contable", "gestor")),
):
    return installments_service.create(db, data, user.id)


@router.post("/{installment_id}/pay", response_model=InstallmentOut)
async def pay_installment(
    installment_id: int,
    data: InstallmentPay,
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
    return installments_service.pay_installment(db, installment_id, data, user, deleg)