"""Router: anticipos y préstamos — M9 Fase 1."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.deps import get_current_user, require_role
from app.schemas.financial_modules import (
    AdvanceLoanCreate,
    AdvanceLoanRepay,
    AdvanceLoanRepayByPayroll,
    AdvanceLoanOut,
)
from app.services import advances_service

router = APIRouter(prefix="/advances-loans", tags=["advances-loans"])


def _resolve_delegation(user, data_delegacion, db: Session) -> str:
    """Resuelve la delegación de la operación en este orden:
       1) data.delegacion si viene explícita en el body (admin elige)
       2) user.delegacion si es Bata o Malabo (gestor)
       3) delegación de la sesión de caja abierta del usuario
       4) HTTP 400 si no se puede determinar
    """
    if data_delegacion in ("Bata", "Malabo"):
        return data_delegacion
    if getattr(user, "delegacion", None) in ("Bata", "Malabo"):
        return user.delegacion
    from app.models import catalogs as _m
    sess = (
        db.query(_m.CashSession)
        .filter(_m.CashSession.user_id == user.id, _m.CashSession.status == "open")
        .first()
    )
    if sess:
        return sess.delegacion
    raise HTTPException(
        status_code=400,
        detail="Debes indicar delegación o tener sesión de caja abierta",
    )


@router.get("", response_model=list[AdvanceLoanOut])
async def list_advances(
    status: Optional[str] = None,
    employee_id: Optional[int] = None,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return advances_service.list_all(db, status=status, employee_id=employee_id)


@router.post("", response_model=AdvanceLoanOut)
async def create_advance(
    data: AdvanceLoanCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role("admin", "contable", "gestor")),
):
    delegacion = _resolve_delegation(user, getattr(data, "delegacion", None), db)
    return advances_service.create(db, data, user, delegacion)


@router.put("/{advance_id}/repay", response_model=AdvanceLoanOut)
async def repay_advance(
    advance_id: int,
    data: AdvanceLoanRepay,
    db: Session = Depends(get_db),
    user=Depends(require_role("admin", "contable", "gestor")),
):
    """Repay manual — el empleado devuelve efectivo a caja. Crea transacción
    ingreso y marca el anticipo como parcial o cerrado."""
    delegacion = _resolve_delegation(user, getattr(data, "delegacion", None), db)
    return advances_service.repay(db, advance_id, data, user, delegacion)


@router.put("/{advance_id}/repay-by-payroll", response_model=AdvanceLoanOut)
async def repay_advance_by_payroll(
    advance_id: int,
    data: AdvanceLoanRepayByPayroll,
    db: Session = Depends(get_db),
    user=Depends(require_role("admin", "contable")),
):
    """Repay automático por descuento en nómina — NO crea transacción. Uso
    interno del service de nómina (M10). Solo admin y contable.

    Este endpoint existe para que cuando M10 genere una nómina con anticipos
    pendientes, pueda marcar esos anticipos como saldados sin generar una
    transacción duplicada — la transacción de caja es la del pago de nómina
    reducido, no una transacción de devolución.
    """
    return advances_service.repay_by_payroll(db, advance_id, data, user.id)
