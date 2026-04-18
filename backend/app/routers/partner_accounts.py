"""Router: cuenta corriente de socios."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.deps import get_current_user, require_role
from app.schemas.financial_modules import (
    PartnerChargeCreate, PartnerContribution, PartnerDividendCompensation,
    PartnerMovementOut, PartnerBalanceOut,
)
from app.services import partner_accounts_service

router = APIRouter(prefix="/partner-accounts", tags=["partner-accounts"])




def _resolve_delegation(user, data_delegacion, db):
    """Orden de prioridad para decidir la delegación de la operación:
       1) data.delegacion si viene en el body
       2) user.delegacion si es Bata o Malabo
       3) sesión de caja abierta del usuario
       4) error 400
    """
    if data_delegacion in ("Bata", "Malabo"):
        return data_delegacion
    if getattr(user, "delegacion", None) in ("Bata", "Malabo"):
        return user.delegacion
    from app.models import catalogs as _m
    sess = (db.query(_m.CashSession)
              .filter(_m.CashSession.user_id == user.id, _m.CashSession.status == "open")
              .first())
    if sess:
        return sess.delegacion
    from fastapi import HTTPException
    raise HTTPException(status_code=400,
        detail="Debes indicar delegación o tener una sesión de caja abierta")


@router.get("/balances", response_model=list[PartnerBalanceOut])
async def list_balances(
    db: Session = Depends(get_db),
    user = Depends(require_role("admin", "contable", "consulta")),
):
    return partner_accounts_service.list_balances(db)


@router.get("/movements", response_model=list[PartnerMovementOut])
async def list_movements(
    partner_id: Optional[int] = None,
    db: Session = Depends(get_db),
    user = Depends(require_role("admin", "contable", "consulta")),
):
    return partner_accounts_service.list_movements(db, partner_id=partner_id)


@router.post("/charge", response_model=PartnerMovementOut)
async def charge(
    data: PartnerChargeCreate,
    db: Session = Depends(get_db),
    user = Depends(require_role("gestor", "admin")),
):
    deleg = _resolve_delegation(user, getattr(data, "delegacion", None), db)
    return partner_accounts_service.charge_partner(db, data, user, deleg)


@router.post("/contribution", response_model=PartnerMovementOut)
async def contribution(
    data: PartnerContribution,
    db: Session = Depends(get_db),
    user = Depends(require_role("admin", "contable")),
):
    deleg = _resolve_delegation(user, getattr(data, "delegacion", None), db)
    return partner_accounts_service.register_contribution(db, data, user, deleg)


@router.post("/compensate", response_model=PartnerMovementOut)
async def compensate(
    data: PartnerDividendCompensation,
    db: Session = Depends(get_db),
    user = Depends(require_role("admin", "contable")),
):
    deleg = _resolve_delegation(user, getattr(data, "delegacion", None), db)
    return partner_accounts_service.compensate_dividends(db, data, user, deleg)