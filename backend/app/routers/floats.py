"""Router: circulantes — M9 Fase 1 Parte D."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.deps import get_current_user, require_role
from app.schemas.financial_modules import FloatCreate, FloatJustify, FloatClose, FloatOut
from app.services import floats_service

router = APIRouter(prefix="/floats", tags=["floats"])


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


@router.get("", response_model=list[FloatOut])
async def list_floats(
    status: Optional[str] = None,
    employee_id: Optional[int] = None,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return floats_service.list_all(db, status=status, employee_id=employee_id)


@router.post("", response_model=FloatOut)
async def create_float(
    data: FloatCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role("admin", "contable", "gestor")),
):
    delegacion = _resolve_delegation(user, getattr(data, "delegacion", None), db)
    return floats_service.create(db, data, user, delegacion)


@router.put("/{float_id}/justify", response_model=FloatOut)
async def justify_float(
    float_id: int,
    data: FloatJustify,
    db: Session = Depends(get_db),
    user=Depends(require_role("admin", "contable", "gestor")),
):
    delegacion = _resolve_delegation(user, getattr(data, "delegacion", None), db)
    return floats_service.justify(db, float_id, data, user, delegacion)


@router.put("/{float_id}/close", response_model=FloatOut)
async def close_float(
    float_id: int,
    data: FloatClose,
    db: Session = Depends(get_db),
    user=Depends(require_role("admin", "contable", "gestor")),
):
    delegacion = _resolve_delegation(user, getattr(data, "delegacion", None), db)
    return floats_service.close_float(db, float_id, data, user, delegacion)
