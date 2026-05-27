"""
Servicio — Retiradas bancarias (flujo 4 pasos).

Workflow:
  1. SOLICITAR  (gestor)   : request_withdrawal()  -> status 'requested'
  2. FORMALIZAR (contable) : formalize()           -> status 'formalized'
  3a. APROBAR  (admin)    : approve()             -> status 'approved'
  3b. RECHAZAR (admin)    : reject()              -> status 'rejected'  (desde requested o formalized)
  4. CONFIRMAR  (gestor)   : confirm()             -> status 'confirmed' + crea Transaction de entrada
"""
from datetime import datetime, timedelta
from typing import Optional, List, Tuple

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.cash_flow import BankWithdrawalRequest, CashSession, Transaction
from app.models.catalogs import CorporateAccount, TransactionCategory, TransactionSubcategory
from app.models.user import User
from app.models.audit_log import AuditLog
from app.schemas.bank_withdrawal import (
    BankWithdrawalRequestCreate, BankWithdrawalFormalize,
    BankWithdrawalApprove, BankWithdrawalReject, BankWithdrawalConfirm,
    BankWithdrawalFilters,
)
from app.config import settings


class BankWithdrawalService:
    def __init__(self, db: Session):
        self.db = db

    # ── Paso 1: SOLICITAR (gestor) ─────────────────────────────────────────
    def request_withdrawal(self, data: BankWithdrawalRequestCreate, user: User) -> BankWithdrawalRequest:
        if user.role != "gestor":
            raise HTTPException(status_code=403, detail="Solo el gestor puede solicitar retiradas bancarias")
        if user.delegacion != data.delegacion:
            raise HTTPException(status_code=403, detail=f"Solo puede solicitar retiradas de {user.delegacion}")

        now = datetime.utcnow()
        w = BankWithdrawalRequest(
            delegacion=data.delegacion,
            amount=data.amount,
            reason=data.reason,
            # Paso 1
            requested_by=user.id, requested_at=now,
            # Backward compat: proposed_by NOT NULL, lo rellenamos = gestor solicitante
            proposed_by=user.id, proposed_at=now,
            status="requested",
            notes=data.notes,
        )
        self.db.add(w)
        self.db.flush()
        self._audit(user, w, "BANK_WITHDRAWAL_REQUESTED")
        self.db.commit()
        self.db.refresh(w)
        return w

    # Alias backward-compat para código antiguo que llame propose()
    propose = request_withdrawal

    # ── Paso 2: FORMALIZAR (contable) ──────────────────────────────────────
    def formalize(self, wid: int, data: BankWithdrawalFormalize, user: User) -> BankWithdrawalRequest:
        if user.role not in ("contable", "admin"):
            raise HTTPException(status_code=403, detail="Solo el contable o admin pueden formalizar retiradas")
        w = self._get_or_404(wid)
        self._require_status(w, "requested", "formalizar")

        account = self.db.query(CorporateAccount).get(data.corporate_account_id)
        if not account:
            raise HTTPException(status_code=404, detail="Cuenta corporativa no encontrada")
        if account.delegacion != w.delegacion:
            raise HTTPException(status_code=400, detail=f"La cuenta pertenece a {account.delegacion}, no a {w.delegacion}")

        w.corporate_account_id = data.corporate_account_id
        w.cheque_reference = data.cheque_reference
        w.formalized_by = user.id
        w.formalized_at = datetime.utcnow()
        w.status = "formalized"
        if data.notes:
            w.notes = (w.notes or "") + f"\n[Formalización] {data.notes}"
        self._audit(user, w, "BANK_WITHDRAWAL_FORMALIZED")
        self.db.commit()
        self.db.refresh(w)
        return w

    # ── Paso 3a: APROBAR (admin) ───────────────────────────────────────────
    def approve(self, wid: int, data: BankWithdrawalApprove, user: User) -> BankWithdrawalRequest:
        self._require_admin(user)
        w = self._get_or_404(wid)
        self._require_status(w, "formalized", "aprobar")
        w.approved_by = user.id
        w.approved_at = datetime.utcnow()
        w.status = "approved"
        if data.notes:
            w.notes = (w.notes or "") + f"\n[Aprobación] {data.notes}"
        self._audit(user, w, "BANK_WITHDRAWAL_APPROVED")
        self.db.commit()
        self.db.refresh(w)
        return w

    # ── Paso 3b: RECHAZAR (admin) ──────────────────────────────────────────
    def reject(self, wid: int, data: BankWithdrawalReject, user: User) -> BankWithdrawalRequest:
        self._require_admin(user)
        w = self._get_or_404(wid)
        if w.status not in ("requested", "formalized"):
            raise HTTPException(status_code=400, detail=f"No se puede rechazar: estado '{w.status}'")
        w.status = "rejected"
        w.rejection_reason = data.rejection_reason
        self._audit(user, w, "BANK_WITHDRAWAL_REJECTED", {"reason": data.rejection_reason})
        self.db.commit()
        self.db.refresh(w)
        return w

    # ── Paso 4: CONFIRMAR (gestor) ─────────────────────────────────────────
    def confirm(self, wid: int, data: BankWithdrawalConfirm, user: User) -> BankWithdrawalRequest:
        if user.role not in ("gestor", "admin"):
            raise HTTPException(status_code=403, detail="Solo el gestor o admin pueden confirmar recepción")
        w = self._get_or_404(wid)
        self._require_status(w, "approved", "confirmar")
        if user.role == "gestor" and user.delegacion != w.delegacion:
            raise HTTPException(status_code=403, detail=f"Solo puede confirmar retiradas de {user.delegacion}")

        active = self.db.query(CashSession).filter(
            CashSession.user_id == user.id, CashSession.status == "open"
        ).first()
        if not active:
            raise HTTPException(status_code=400, detail="Necesita una sesión abierta para confirmar")

        tx = self._create_bank_income(w, active, user)
        w.confirmed_by = user.id
        w.confirmed_at = datetime.utcnow()
        w.session_id = active.id
        w.status = "confirmed"
        if data.notes:
            w.notes = (w.notes or "") + f"\n[Recepción] {data.notes}"
        self._audit(user, w, "BANK_WITHDRAWAL_CONFIRMED", {"transaction_id": tx.id})
        self.db.commit()
        self.db.refresh(w)
        return w

    # ── Cancelar (gestor que solicitó, mientras esté en 'requested') ───────
    def cancel(self, wid: int, user: User) -> BankWithdrawalRequest:
        w = self._get_or_404(wid)
        self._require_status(w, "requested", "cancelar")
        if user.role == "gestor" and w.requested_by != user.id:
            raise HTTPException(status_code=403, detail="Solo el solicitante o un admin pueden cancelar")
        if user.role not in ("gestor", "admin"):
            raise HTTPException(status_code=403, detail="Solo gestor o admin pueden cancelar")
        w.status = "rejected"
        w.rejection_reason = f"Cancelada por {user.full_name or user.username}"
        self._audit(user, w, "BANK_WITHDRAWAL_CANCELLED")
        self.db.commit()
        self.db.refresh(w)
        return w

    # ── Lecturas ───────────────────────────────────────────────────────────
    def get_by_id(self, wid: int) -> BankWithdrawalRequest:
        return self._get_or_404(wid)

    def list_withdrawals(self, f: BankWithdrawalFilters, user: User) -> Tuple[List[dict], int]:
        q = self.db.query(BankWithdrawalRequest)
        if user.role == "gestor":
            q = q.filter(BankWithdrawalRequest.delegacion == user.delegacion)
        if f.delegacion:
            q = q.filter(BankWithdrawalRequest.delegacion == f.delegacion)
        if f.status:
            q = q.filter(BankWithdrawalRequest.status == f.status)
        if f.date_start:
            q = q.filter(BankWithdrawalRequest.proposed_at >= f.date_start)
        if f.date_end:
            q = q.filter(BankWithdrawalRequest.proposed_at <= f.date_end)
        total = q.count()
        items = q.order_by(BankWithdrawalRequest.proposed_at.desc()).offset(
            (f.page - 1) * f.page_size).limit(f.page_size).all()
        return [self.enrich(w) for w in items], total

    def count_my_pending(self, user: User) -> int:
        """Cuenta lo que le toca actuar al usuario según su rol."""
        q = self.db.query(BankWithdrawalRequest)
        if user.role == "contable":
            q = q.filter(BankWithdrawalRequest.status == "requested")
        elif user.role == "admin":
            q = q.filter(BankWithdrawalRequest.status == "formalized")
        elif user.role == "gestor":
            q = q.filter(
                BankWithdrawalRequest.status == "approved",
                BankWithdrawalRequest.delegacion == user.delegacion,
            )
        else:
            return 0
        return q.count()

    # Alias backward-compat
    def count_pending(self, delegacion: Optional[str] = None) -> int:
        q = self.db.query(BankWithdrawalRequest).filter(
            BankWithdrawalRequest.status.in_(["requested", "formalized", "approved"])
        )
        if delegacion:
            q = q.filter(BankWithdrawalRequest.delegacion == delegacion)
        return q.count()

    def enrich(self, w) -> dict:
        def _name(uid):
            if not uid:
                return None
            u = self.db.query(User).get(uid)
            return u.full_name if u else "—"
        acc = self.db.query(CorporateAccount).get(w.corporate_account_id) if w.corporate_account_id else None
        return {
            "id": w.id, "delegacion": w.delegacion,
            "corporate_account_id": w.corporate_account_id,
            "account_bank_name": acc.bank_name if acc else None,
            "account_number": acc.account_number if acc else None,
            "amount": float(w.amount), "cheque_reference": w.cheque_reference,
            # Flujo 4 pasos
            "requested_by": w.requested_by, "requested_by_name": _name(w.requested_by),
            "requested_at": w.requested_at,
            "reason": w.reason,
            "formalized_by": w.formalized_by, "formalized_by_name": _name(w.formalized_by),
            "formalized_at": w.formalized_at,
            # Backward compat
            "proposed_by": w.proposed_by, "proposed_by_name": _name(w.proposed_by),
            "proposed_at": w.proposed_at,
            "approved_by": w.approved_by, "approved_by_name": _name(w.approved_by),
            "approved_at": w.approved_at,
            "confirmed_by": w.confirmed_by, "confirmed_by_name": _name(w.confirmed_by),
            "confirmed_at": w.confirmed_at,
            "session_id": w.session_id, "status": w.status,
            "rejection_reason": w.rejection_reason, "notes": w.notes,
        }

    # ── Helpers internos ───────────────────────────────────────────────────
    def _get_or_404(self, wid):
        w = self.db.query(BankWithdrawalRequest).get(wid)
        if not w:
            raise HTTPException(status_code=404, detail=f"Retirada {wid} no encontrada")
        return w

    def _require_admin(self, u):
        if u.role != "admin":
            raise HTTPException(status_code=403, detail="Solo el Administrador")

    def _require_status(self, w, expected, action):
        if w.status != expected:
            raise HTTPException(status_code=400, detail=f"No se puede {action}: estado '{w.status}'")

    def _create_bank_income(self, w, session, user):
        from app.services.integrity_service import compute_transaction_hash
        from app.services.reference_service import generate_reference

        acc = self.db.query(CorporateAccount).get(w.corporate_account_id) if w.corporate_account_id else None
        now = datetime.utcnow()
        cat = self.db.query(TransactionCategory).filter(TransactionCategory.name == "Transferencia_entrada").first()
        subcat = None
        if cat:
            subcat = self.db.query(TransactionSubcategory).filter(
                TransactionSubcategory.category_id == cat.id
            ).first()
        ref = generate_reference(self.db, w.delegacion)

        tx = Transaction(
            session_id=session.id, delegacion=w.delegacion,
            category_id=cat.id if cat else 1, subcategory_id=subcat.id if subcat else 1,
            user_id=user.id,
            counterparty_free=f"{acc.bank_name} — {acc.account_number}" if acc else "Banco",
            type="income", amount=w.amount,
            concept=f"Retirada bancaria — Cheque {w.cheque_reference or '?'}",
            reference_number=ref, transaction_type="bank_income",
            approval_status="approved", imported=False,
            editable_until=now + timedelta(minutes=settings.EDIT_WINDOW_MINUTES),
            created_at=now, integrity_hash="",
        )
        self.db.add(tx)
        self.db.flush()
        tx.integrity_hash = compute_transaction_hash(tx)
        self.db.flush()
        return tx

    def _audit(self, user, w, action, details=None):
        self.db.add(AuditLog(
            user_id=user.id, delegacion=w.delegacion,
            action=action, entity="bank_withdrawal_request",
            entity_id=w.id, details=details,
        ))
