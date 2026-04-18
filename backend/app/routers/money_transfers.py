"""Router: envíos de dinero."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.deps import get_current_user, require_role
from app.schemas.financial_modules import MoneyTransferCreate, MoneyTransferOut, InterDelegationPositionOut
from app.services import money_transfers_service

router = APIRouter(prefix="/money-transfers", tags=["money-transfers"])


@router.get("", response_model=list[MoneyTransferOut])
async def list_all(
    operator: Optional[str] = None,
    direction: Optional[str] = None,
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    return money_transfers_service.list_all(db, operator=operator, direction=direction)


@router.post("", response_model=MoneyTransferOut)
async def create(
    data: MoneyTransferCreate,
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
    return money_transfers_service.create(db, data, user, deleg)


@router.get("/inter-delegation-position", response_model=InterDelegationPositionOut)
async def position(
    db: Session = Depends(get_db),
    user = Depends(require_role("admin", "contable", "consulta")),
):
    return money_transfers_service.inter_delegation_position(db)