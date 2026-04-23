"""
Router — /sessions — Sesiones de caja.
"""
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from app.core.deps import get_db, get_current_user, require_role
from app.models.user import User
from app.models.cash_flow import Transaction
from app.schemas.cash_session import CashSessionRead, CashSessionOpen, CashSessionClose, CashSessionFilters
from app.services.session_service import SessionService

router = APIRouter(prefix="/sessions", tags=["Sesiones de caja"])


def _to_read(s, db, svc, user_obj=None) -> CashSessionRead:
    inc, exp = svc.session_totals(s.id)
    u = user_obj or db.query(User).get(s.user_id)
    tx_count = db.query(Transaction).filter(Transaction.session_id == s.id).count()
    return CashSessionRead(
        id=s.id, user_id=s.user_id, delegacion=s.delegacion,
        opened_at=s.opened_at, closed_at=s.closed_at,
        opening_balance=float(s.opening_balance),
        closing_balance=float(s.closing_balance) if s.closing_balance is not None else None,
        status=s.status, notes=s.notes,
        user_full_name=u.full_name if u else "—",
        transaction_count=tx_count, total_income=inc, total_expense=exp,
    )


@router.post("", response_model=CashSessionRead, status_code=201)
async def open_session(data: CashSessionOpen, db: Session = Depends(get_db),
                       user: User = Depends(require_role("gestor"))):
    svc = SessionService(db)
    return _to_read(svc.open_session(data, user), db, svc, user)


@router.put("/{session_id}/close", response_model=CashSessionRead)
async def close_session(session_id: int, data: CashSessionClose, db: Session = Depends(get_db),
                        user: User = Depends(get_current_user)):
    svc = SessionService(db)
    return _to_read(svc.close_session(session_id, data, user), db, svc)


@router.get("/active", response_model=Optional[CashSessionRead])
async def get_active(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    svc = SessionService(db)
    s = svc.get_active(user.id)
    return _to_read(s, db, svc, user) if s else None


@router.get("")
async def list_sessions(
    delegacion: Optional[str] = Query(None),
    user_id: Optional[int] = Query(None),
    session_status: Optional[str] = Query(None, alias="status"),
    date_start: Optional[str] = Query(None),
    date_end: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db), user: User = Depends(get_current_user),
):
    f = CashSessionFilters(
        delegacion=delegacion, user_id=user_id, status=session_status,
        date_start=datetime.fromisoformat(date_start) if date_start else None,
        date_end=datetime.fromisoformat(date_end) if date_end else None,
        page=page, page_size=page_size,
    )
    svc = SessionService(db)
    items, total = svc.list_sessions(f, user)
    return {"items": items, "total": total, "page": page,
            "page_size": page_size, "pages": (total + page_size - 1) // page_size}


@router.get("/{session_id}", response_model=CashSessionRead)
async def get_session(session_id: int, db: Session = Depends(get_db),
                      user: User = Depends(get_current_user)):
    svc = SessionService(db)
    s = svc.get_by_id(session_id)
    if user.role == "gestor" and s.delegacion != user.delegacion:
        raise HTTPException(status_code=403, detail="Sin acceso a esta sesión")
    return _to_read(s, db, svc)
