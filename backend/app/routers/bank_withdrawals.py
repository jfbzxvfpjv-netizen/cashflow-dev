"""
Router — /bank-withdrawals — Retiradas bancarias (flujo 4 pasos).

  POST   /                          gestor          SOLICITAR
  PUT    /{wid}/formalize           contable|admin  FORMALIZAR (añade cuenta + cheque)
  PUT    /{wid}/approve             admin           APROBAR
  PUT    /{wid}/reject              admin           RECHAZAR (desde requested o formalized)
  PUT    /{wid}/cancel              gestor|admin    CANCELAR (solo mientras esté en requested)
  PUT    /{wid}/confirm             gestor|admin    CONFIRMAR recepción física
  GET    /                          todos           Listar (gestor solo su delegación)
  GET    /pending-count             todos           Cuenta lo que le toca actuar al usuario
  GET    /{wid}                     todos           Detalle (gestor solo su delegación)
"""
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user, require_role
from app.models.user import User
from app.schemas.bank_withdrawal import (
    BankWithdrawalRead,
    BankWithdrawalRequestCreate,
    BankWithdrawalFormalize,
    BankWithdrawalApprove,
    BankWithdrawalReject,
    BankWithdrawalConfirm,
    BankWithdrawalFilters,
)
from app.services.bank_withdrawal_service import BankWithdrawalService

router = APIRouter(prefix="/bank-withdrawals", tags=["Retiradas bancarias"])


# ── Paso 1: SOLICITAR (gestor) ─────────────────────────────────────────────
@router.post("", response_model=BankWithdrawalRead, status_code=201)
async def request_withdrawal(
    data: BankWithdrawalRequestCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("gestor")),
):
    svc = BankWithdrawalService(db)
    return svc.enrich(svc.request_withdrawal(data, user))


# ── Paso 2: FORMALIZAR (contable o admin) ──────────────────────────────────
@router.put("/{wid}/formalize", response_model=BankWithdrawalRead)
async def formalize(
    wid: int,
    data: BankWithdrawalFormalize,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if user.role not in ("contable", "admin"):
        raise HTTPException(status_code=403, detail="Solo contable o admin pueden formalizar")
    svc = BankWithdrawalService(db)
    return svc.enrich(svc.formalize(wid, data, user))


# ── Paso 3a: APROBAR (admin) ───────────────────────────────────────────────
@router.put("/{wid}/approve", response_model=BankWithdrawalRead)
async def approve(
    wid: int,
    data: BankWithdrawalApprove,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("admin")),
):
    svc = BankWithdrawalService(db)
    return svc.enrich(svc.approve(wid, data, user))


# ── Paso 3b: RECHAZAR (admin) ──────────────────────────────────────────────
@router.put("/{wid}/reject", response_model=BankWithdrawalRead)
async def reject(
    wid: int,
    data: BankWithdrawalReject,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("admin")),
):
    svc = BankWithdrawalService(db)
    return svc.enrich(svc.reject(wid, data, user))


# ── Cancelar (gestor solicitante o admin) ──────────────────────────────────
@router.put("/{wid}/cancel", response_model=BankWithdrawalRead)
async def cancel(
    wid: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    svc = BankWithdrawalService(db)
    return svc.enrich(svc.cancel(wid, user))


# ── Paso 4: CONFIRMAR (gestor o admin) ─────────────────────────────────────
@router.put("/{wid}/confirm", response_model=BankWithdrawalRead)
async def confirm(
    wid: int,
    data: BankWithdrawalConfirm,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    svc = BankWithdrawalService(db)
    return svc.enrich(svc.confirm(wid, data, user))


# ── Listado ────────────────────────────────────────────────────────────────
@router.get("")
async def list_withdrawals(
    delegacion: Optional[str] = Query(None),
    withdrawal_status: Optional[str] = Query(None, alias="status"),
    date_start: Optional[str] = Query(None),
    date_end: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if user.role not in ("contable", "admin", "gestor"):
        raise HTTPException(status_code=403, detail="Acceso no permitido")
    f = BankWithdrawalFilters(
        delegacion=delegacion, status=withdrawal_status,
        date_start=datetime.fromisoformat(date_start) if date_start else None,
        date_end=datetime.fromisoformat(date_end) if date_end else None,
        page=page, page_size=page_size,
    )
    svc = BankWithdrawalService(db)
    items, total = svc.list_withdrawals(f, user)
    return {
        "items": items, "total": total, "page": page,
        "page_size": page_size, "pages": (total + page_size - 1) // page_size,
    }


# ── Badge: cuenta lo que le toca actuar al usuario ─────────────────────────
@router.get("/pending-count")
async def pending_count(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return {"pending_count": BankWithdrawalService(db).count_my_pending(user)}


# ── Detalle ────────────────────────────────────────────────────────────────
@router.get("/{wid}", response_model=BankWithdrawalRead)
async def get_withdrawal(
    wid: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    svc = BankWithdrawalService(db)
    w = svc.get_by_id(wid)
    if user.role == "gestor" and w.delegacion != user.delegacion:
        raise HTTPException(status_code=403, detail="Sin acceso")
    return svc.enrich(w)
