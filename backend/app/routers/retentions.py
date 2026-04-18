"""Router: retenciones y depósitos — M9 Fase 1 Parte C."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.deps import get_current_user, require_role
from app.schemas.financial_modules import (
    RetentionDepositCreate,
    RetentionDepositRelease,
    RetentionDepositOut,
)
from app.services import retentions_service

router = APIRouter(prefix="/retentions-deposits", tags=["retentions-deposits"])


def _resolve_delegation(user, data_delegacion, db: Session) -> str:
    """Resuelve delegación: body > user.delegacion > sesión abierta."""
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


@router.get("", response_model=list[RetentionDepositOut])
async def list_items(
    status: Optional[str] = None,
    type: Optional[str] = None,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return retentions_service.list_all(db, status=status, type_=type)


@router.post("", response_model=RetentionDepositOut)
async def create_item(
    data: RetentionDepositCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role("admin", "contable", "gestor")),
):
    delegacion = _resolve_delegation(user, getattr(data, "delegacion", None), db)
    return retentions_service.create(db, data, user, delegacion)


@router.put("/{item_id}/release", response_model=RetentionDepositOut)
async def release_item(
    item_id: int,
    data: RetentionDepositRelease,
    db: Session = Depends(get_db),
    user=Depends(require_role("admin", "contable", "gestor")),
):
    """Libera el registro creando la transacción correspondiente:
      - deposit: transacción ingreso (vuelve dinero del tercero).
      - retention: transacción egreso (sale dinero al destinatario).
    """
    delegacion = _resolve_delegation(user, getattr(data, "delegacion", None), db)
    return retentions_service.release(db, item_id, data, user, delegacion)
