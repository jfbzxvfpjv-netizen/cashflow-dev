"""
Servicio — Sesiones de caja.
"""
from datetime import datetime
from typing import Optional, List, Tuple

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.cash_flow import CashSession, Transaction, TransactionAttachment
from app.models.user import User
from app.schemas.cash_session import CashSessionOpen, CashSessionClose, CashSessionFilters
from app.services.config_service import ConfigService


class SessionService:
    def __init__(self, db: Session):
        self.db = db
        self.config_svc = ConfigService(db)

    def open_session(self, data: CashSessionOpen, user: User) -> CashSession:
        if user.role not in ("gestor", "admin"):
            raise HTTPException(status_code=403, detail="Solo Gestor y Admin pueden abrir sesiones")

        delegacion = self._resolve_delegacion(data.delegacion, user)

        if self.get_active(user.id):
            raise HTTPException(status_code=409, detail="Ya tiene una sesión abierta. Ciérrela primero.")

        config = self.config_svc.get_by_delegacion(delegacion)
        if not config:
            raise HTTPException(status_code=400, detail=f"Configure el saldo inicial de {delegacion} primero.")

        opening_balance = self.config_svc.get_current_balance(delegacion)
        session = CashSession(
            user_id=user.id, delegacion=delegacion,
            opened_at=datetime.utcnow(), opening_balance=opening_balance,
            status="open", notes=data.notes,
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def close_session(self, session_id: int, data: CashSessionClose, user: User) -> CashSession:
        session = self._get_or_404(session_id)
        if session.user_id != user.id and user.role != "admin":
            raise HTTPException(status_code=403, detail="Solo el titular o el Admin pueden cerrar la sesión")
        if session.status == "closed":
            raise HTTPException(status_code=400, detail="La sesión ya está cerrada")

        inc, exp = self.session_totals(session_id)
        session.closing_balance = float(session.opening_balance) + inc - exp
        session.closed_at = datetime.utcnow()
        session.status = "closed"
        if data.notes:
            session.notes = (session.notes or "") + f"\n[Cierre] {data.notes}"
        self._lock_attachments(session_id)
        self.db.commit()
        self.db.refresh(session)
        return session

    def get_by_id(self, sid: int) -> CashSession:
        return self._get_or_404(sid)

    def get_active(self, user_id: int) -> Optional[CashSession]:
        return self.db.query(CashSession).filter(
            CashSession.user_id == user_id, CashSession.status == "open"
        ).first()

    def list_sessions(self, f: CashSessionFilters, user: User) -> Tuple[List[dict], int]:
        q = self.db.query(CashSession)
        if user.role == "gestor":
            q = q.filter(CashSession.delegacion == user.delegacion)
        if f.delegacion:
            q = q.filter(CashSession.delegacion == f.delegacion)
        if f.user_id:
            q = q.filter(CashSession.user_id == f.user_id)
        if f.status:
            q = q.filter(CashSession.status == f.status)
        if f.date_start:
            q = q.filter(CashSession.opened_at >= f.date_start)
        if f.date_end:
            q = q.filter(CashSession.opened_at <= f.date_end)

        total = q.count()
        sessions = q.order_by(CashSession.opened_at.desc()).offset(
            (f.page - 1) * f.page_size).limit(f.page_size).all()

        results = []
        for s in sessions:
            u = self.db.query(User).get(s.user_id)
            inc, exp = self.session_totals(s.id)
            tx_count = self.db.query(Transaction).filter(Transaction.session_id == s.id).count()
            results.append({
                "id": s.id, "user_id": s.user_id,
                "user_full_name": u.full_name if u else "—",
                "delegacion": s.delegacion,
                "opened_at": s.opened_at, "closed_at": s.closed_at,
                "opening_balance": float(s.opening_balance),
                "closing_balance": float(s.closing_balance) if s.closing_balance is not None else None,
                "status": s.status, "notes": s.notes,
                "transaction_count": tx_count, "total_income": inc, "total_expense": exp,
            })
        return results, total

    def session_totals(self, sid: int) -> Tuple[float, float]:
        base = self.db.query(func.coalesce(func.sum(Transaction.amount), 0)).filter(
            Transaction.session_id == sid, Transaction.cancelled == False,
            Transaction.approval_status == "approved",
        )
        return float(base.filter(Transaction.type == "income").scalar()), \
               float(base.filter(Transaction.type == "expense").scalar())

    def _get_or_404(self, sid):
        s = self.db.query(CashSession).get(sid)
        if not s:
            raise HTTPException(status_code=404, detail=f"Sesión {sid} no encontrada")
        return s

    def _resolve_delegacion(self, requested: Optional[str], user: User) -> str:
        if user.role == "gestor":
            if requested and requested != user.delegacion:
                raise HTTPException(status_code=403, detail=f"Solo puede operar en {user.delegacion}")
            return user.delegacion
        if user.role == "admin":
            if not requested:
                raise HTTPException(status_code=400, detail="Indique la delegación al abrir sesión")
            return requested
        raise HTTPException(status_code=403, detail="Su perfil no permite abrir sesiones")

    def _lock_attachments(self, sid):
        tx_ids = [t.id for t in self.db.query(Transaction.id).filter(Transaction.session_id == sid).all()]
        if tx_ids:
            self.db.query(TransactionAttachment).filter(
                TransactionAttachment.transaction_id.in_(tx_ids)
            ).update({"locked": True}, synchronize_session="fetch")
