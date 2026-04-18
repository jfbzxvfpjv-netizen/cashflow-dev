"""Router M9 — Operaciones en divisa."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.deps import get_current_user, require_role
from app.services import currency_service
from app.schemas.financial_modules import (
    CurrencyBuy,
    CurrencyDeliver,
    CurrencyEdit,
    CurrencyCancel,
    CurrencyOperationOut,
    EurStockOut,
)

router = APIRouter(prefix="/currency-ops", tags=["currency-ops"])


def _resolve_delegation(user, data_delegacion, db):
    """Orden de prioridad para decidir la delegación de la operación:
       1) data.delegacion si viene en el body (admin elige explícitamente)
       2) user.delegacion si es Bata o Malabo (gestores)
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
    raise HTTPException(
        status_code=400,
        detail="Debes indicar delegación o tener una sesión de caja abierta"
    )


@router.get("", response_model=list[CurrencyOperationOut])
async def list_operations(
    delegacion: Optional[str] = None,
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    return currency_service.list_operations(db, delegacion=delegacion)


@router.get("/eur-stock/{delegacion}", response_model=EurStockOut)
async def get_eur_stock(
    delegacion: str,
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    return currency_service.get_stock(db, delegacion)


@router.post("/buy", response_model=CurrencyOperationOut)
async def buy_euros(
    data: CurrencyBuy,
    db: Session = Depends(get_db),
    user = Depends(require_role("gestor", "admin")),
):
    deleg = _resolve_delegation(user, getattr(data, "delegacion", None), db)
    return currency_service.buy_euros(db, data, user, deleg)


@router.post("/deliver", response_model=CurrencyOperationOut)
async def deliver_euros(
    data: CurrencyDeliver,
    db: Session = Depends(get_db),
    user = Depends(require_role("gestor", "admin")),
):
    deleg = _resolve_delegation(user, getattr(data, "delegacion", None), db)
    return currency_service.deliver_euros(db, data, user, deleg)


@router.put("/{op_id}", response_model=CurrencyOperationOut)
async def edit_delivery(
    op_id: int,
    data: CurrencyEdit,
    db: Session = Depends(get_db),
    user = Depends(require_role("gestor", "admin")),
):
    return currency_service.edit_delivery(db, op_id, data, user)


@router.post("/{op_id}/cancel", response_model=CurrencyOperationOut)
async def cancel_operation(
    op_id: int,
    data: CurrencyCancel,
    db: Session = Depends(get_db),
    user = Depends(require_role("gestor", "admin")),
):
    return currency_service.cancel_operation(db, op_id, data, user)