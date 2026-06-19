"""
Servicio M10b — Nóminas.

Workflow:
  1. generate_period(year, month, delegacion, user)
     -> crea PayrollPeriod en 'draft' + N PayrollEntries (snapshot salarios)
  2. update_entry(entry_id, payload, user)
     -> editar cash_amount/notes mientras periodo esté en 'draft'
  3. execute_entries(period_id, payload, user)
     -> crea Transactions vía financial_helpers (aplica umbral M10a)
  4. close_period(period_id, user)
     -> marca como 'paid' cuando todas las entries con cash_amount > 0 pagadas
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Tuple

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.payroll import PayrollPeriod, PayrollEntry
from app.models.catalogs import Employee
from app.models.financial_modules import RetentionDeposit
from app.models.cash_flow import Transaction
from app.models.user import User
from app.models.audit_log import AuditLog
from app.schemas.financial_modules import AdvanceLoanRepayByPayroll
from app.services.payroll_deductions import calculate_deductions
from app.services.financial_helpers import get_active_session, create_transaction
from app.schemas.payroll import (
    PayrollPeriodCreate, PayrollEntryUpdate, PayrollExecutePayload, PayrollExecuteResult,
)


# Catálogos fijos para nómina (segun pliego v1)
NOMINA_CATEGORY_ID    = 29   # Nominas_Personal
NOMINA_SUBCATEGORY_ID = 100  # Salarios
NOMINA_PROJECT_ID     = 18   # General
NOMINA_WORK_ID        = 107  # Administracion


class PayrollService:
    def __init__(self, db: Session):
        self.db = db


    @staticmethod
    def _apply_cap_to_refs(total, available, refs_list, amount_key):
        if total <= 0 or not refs_list:
            return Decimal(0), available
        if total <= available:
            return total, available - total
        remaining = available
        applied = Decimal(0)
        for r in refs_list:
            requested = Decimal(r[amount_key])
            if remaining <= 0:
                r[amount_key] = "0"
                continue
            take = min(requested, remaining)
            r[amount_key] = str(take)
            applied += take
            remaining -= take
        return applied, remaining

    # ── 1. Generar periodo ─────────────────────────────────────────────────
    def generate_period(self, data: PayrollPeriodCreate, user: User) -> PayrollPeriod:
        if user.role not in ("admin", "contable"):
            raise HTTPException(status_code=403, detail="Solo admin o contable pueden generar periodos de nómina")

        existing = self.db.query(PayrollPeriod).filter(
            PayrollPeriod.year == data.year,
            PayrollPeriod.month == data.month,
            PayrollPeriod.delegacion == data.delegacion,
        ).first()
        if existing:
            raise HTTPException(status_code=409, detail=f"Ya existe periodo {data.year}-{data.month:02d} para {data.delegacion}")

        period = PayrollPeriod(
            year=data.year, month=data.month, delegacion=data.delegacion,
            status="draft", created_by=user.id, created_at=datetime.utcnow(),
            notes=data.notes,
        )
        self.db.add(period)
        self.db.flush()

        employees = self.db.query(Employee).filter(
            Employee.delegacion == data.delegacion,
            Employee.active == True,
        ).all()

        for emp in employees:
            gross = Decimal(emp.salary_gross or 0)
            transfer = Decimal(emp.salary_transfer or 0)
            deds = calculate_deductions(self.db, emp.id, data.year, data.month)
            available = gross - transfer
            adv_capped, available = self._apply_cap_to_refs(deds['advances'], available, deds['refs'].get('advances') or [], 'amount')
            ret_capped, available = self._apply_cap_to_refs(deds['retentions'], available, deds['refs'].get('retentions') or [], 'amount')
            loans_capped, available = self._apply_cap_to_refs(deds['loans'], available, deds['refs'].get('loans') or [], 'amount')
            cash = available
            entry = PayrollEntry(
                period_id=period.id, employee_id=emp.id,
                salary_gross=gross, salary_transfer=transfer, cash_amount=cash,
                deduction_advances=adv_capped, deduction_loans=loans_capped,
                deduction_retentions=ret_capped, deduction_refs=deds['refs'],
                manual_override=False,
            )
            self.db.add(entry)

        self.db.add(AuditLog(
            user_id=user.id, delegacion=data.delegacion,
            action="PAYROLL_PERIOD_GENERATED", entity="payroll_period",
            entity_id=period.id,
            details={"year": data.year, "month": data.month, "employees": len(employees)},
        ))
        self.db.commit()
        self.db.refresh(period)
        return period

    # ── 2. Listado de periodos ─────────────────────────────────────────────
    def list_periods(self, year: Optional[int] = None, delegacion: Optional[str] = None,
                     status: Optional[str] = None, user: Optional[User] = None) -> List[dict]:
        q = self.db.query(PayrollPeriod)
        if year:        q = q.filter(PayrollPeriod.year == year)
        if delegacion:  q = q.filter(PayrollPeriod.delegacion == delegacion)
        if status:      q = q.filter(PayrollPeriod.status == status)
        if user and user.role == "gestor":
            q = q.filter(PayrollPeriod.delegacion == user.delegacion)

        periods = q.order_by(PayrollPeriod.year.desc(), PayrollPeriod.month.desc()).all()
        return [self._enrich_period(p) for p in periods]

    # ── 3. Detalle periodo con entries ─────────────────────────────────────
    def get_period_detail(self, period_id: int, user: User) -> dict:
        period = self._get_or_404(period_id)
        if user.role == "gestor" and period.delegacion != user.delegacion:
            raise HTTPException(status_code=403, detail="Sin acceso a este periodo")

        entries = self.db.query(PayrollEntry).filter(PayrollEntry.period_id == period.id).all()
        result = self._enrich_period(period)
        result["entries"] = [self._enrich_entry(e) for e in entries]
        return result

    # ── 4. Editar entrada (solo si periodo en 'draft') ─────────────────────
    def update_entry(self, entry_id: int, data: PayrollEntryUpdate, user: User) -> PayrollEntry:
        if user.role not in ("admin", "contable"):
            raise HTTPException(status_code=403, detail="Solo admin o contable pueden editar entradas de nómina")

        entry = self.db.query(PayrollEntry).filter(PayrollEntry.id == entry_id).first()
        if not entry:
            raise HTTPException(status_code=404, detail="Entrada no encontrada")
        period = self._get_or_404(entry.period_id)
        if period.status != "draft":
            raise HTTPException(status_code=400, detail=f"Periodo no editable (status='{period.status}')")
        if entry.transaction_id:
            raise HTTPException(status_code=400, detail="No se puede editar: entrada ya pagada")

        if data.cash_amount is not None and Decimal(data.cash_amount) != Decimal(entry.cash_amount or 0):
            entry.cash_amount = data.cash_amount
            entry.manual_override = True
        if data.notes is not None:
            entry.notes = data.notes

        self.db.commit()
        self.db.refresh(entry)
        return entry

    # ── 5. Pagar entrada individual con firma (gestor) ─────────────────────
    def pay_entry(self, period_id: int, entry_id: int, signature_payload: dict, user: User) -> dict:
        """Gestor paga una entrada individual de nómina con firma del empleado.

        Reusa transaction_service.create_transaction que hace toda la cadena:
        transaction + signature + hook M10a (umbral) + audit. Solo gestores pueden
        ejecutar (la política se aplica en transaction_service).
        """
        from app.services.transaction_service import TransactionService

        period = self._get_or_404(period_id)
        if period.status != "draft":
            raise HTTPException(status_code=400, detail=f"Periodo ya cerrado (status='{period.status}')")

        entry = self.db.query(PayrollEntry).filter(
            PayrollEntry.id == entry_id,
            PayrollEntry.period_id == period.id,
        ).first()
        if not entry:
            raise HTTPException(status_code=404, detail="Entrada no encontrada")
        if entry.transaction_id:
            raise HTTPException(status_code=400, detail="Esta nómina ya fue pagada")
        if entry.cash_amount <= 0:
            raise HTTPException(status_code=400, detail="Sin importe en efectivo para pagar")

        emp = self.db.query(Employee).filter(Employee.id == entry.employee_id).first()
        if not emp:
            raise HTTPException(status_code=404, detail="Empleado no encontrado")

        month_str = f"{period.year}-{period.month:02d}"
        # Construir data como espera transaction_service
        data = {
            "type": "expense",
            "amount": float(entry.cash_amount),
            "concept": f"Nómina {month_str} — {emp.full_name}",
            "category_id": NOMINA_CATEGORY_ID,
            "subcategory_id": NOMINA_SUBCATEGORY_ID,
            "projects": [{"project_id": NOMINA_PROJECT_ID, "work_id": NOMINA_WORK_ID}],
            "employee_id": emp.id,
            "supplier_id": None,
            "partner_id": None,
            "counterparty_free": None,
            "vehicle_id": None,
            "signature": signature_payload,
        }

        try:
            txn = TransactionService.create_transaction(self.db, data, user)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        # Vincular entry a la transacción
        entry.transaction_id = txn.id
        entry.paid_at = datetime.utcnow()

        # M10b-v2: liquidacion automatica de anticipos/prestamos/retenciones
        if not entry.manual_override and entry.deduction_refs:
            from app.schemas.financial_modules import AdvanceLoanRepayByPayroll
            from app.services import advances_service
            refs = entry.deduction_refs or {}
            for adv in (refs.get('advances') or []):
                try:
                    advances_service.repay_by_payroll(
                        self.db, adv['advance_id'],
                        AdvanceLoanRepayByPayroll(amount=Decimal(adv['amount'])),
                        user.id,
                    )
                except Exception as ex:
                    self.db.add(AuditLog(
                        user_id=user.id, delegacion=period.delegacion,
                        action="PAYROLL_DEDUCTION_ERROR", entity="advance_loan",
                        entity_id=adv['advance_id'],
                        details={"error": str(ex), "intended_amount": adv['amount']},
                    ))
            for loan in (refs.get('loans') or []):
                try:
                    advances_service.repay_by_payroll(
                        self.db, loan['loan_id'],
                        AdvanceLoanRepayByPayroll(amount=Decimal(loan['amount'])),
                        user.id,
                    )
                except Exception as ex:
                    self.db.add(AuditLog(
                        user_id=user.id, delegacion=period.delegacion,
                        action="PAYROLL_DEDUCTION_ERROR", entity="advance_loan",
                        entity_id=loan['loan_id'],
                        details={"error": str(ex), "intended_amount": loan['amount']},
                    ))
            from sqlalchemy import text as _sa_text
            for ret in (refs.get('retentions') or []):
                try:
                    self.db.execute(_sa_text("""
                        UPDATE retentions_deposits
                        SET status='released', released_at=NOW(), release_transaction_id=:tid
                        WHERE id=:rid AND status='pending'
                    """), {'tid': txn.id, 'rid': ret['retention_id']})
                except Exception as ex:
                    self.db.add(AuditLog(
                        user_id=user.id, delegacion=period.delegacion,
                        action="PAYROLL_DEDUCTION_ERROR", entity="retention_deposit",
                        entity_id=ret['retention_id'],
                        details={"error": str(ex), "intended_amount": ret['amount']},
                    ))

        self.db.add(AuditLog(
            user_id=user.id, delegacion=period.delegacion,
            action="PAYROLL_ENTRY_PAID", entity="payroll_entry",
            entity_id=entry.id,
            details={"transaction_id": txn.id, "employee_id": emp.id, "amount": float(entry.cash_amount)},
        ))
        self.db.commit()

        return {
            "entry_id": entry.id,
            "transaction_id": txn.id,
            "transaction_reference": txn.reference_number,
            "approval_status": txn.approval_status,
        }

    # ── 5b. Lanzar pagos masivo OBSOLETO — placeholder para no romper imports ────
    def execute_entries(self, period_id: int, payload: PayrollExecutePayload, user: User) -> PayrollExecuteResult:
        if user.role not in ("gestor", "admin"):
            raise HTTPException(status_code=403, detail="Solo gestor o admin pueden lanzar pagos de nómina")

        period = self._get_or_404(period_id)
        if user.role == "gestor" and period.delegacion != user.delegacion:
            raise HTTPException(status_code=403, detail=f"Sin acceso a nómina de {period.delegacion}")
        if period.status != "draft":
            raise HTTPException(status_code=400, detail=f"Periodo ya cerrado (status='{period.status}')")

        # Sesión de caja activa (requerida por create_transaction)
        session = get_active_session(self.db, user_id=user.id, delegacion=period.delegacion)

        q = self.db.query(PayrollEntry).filter(
            PayrollEntry.period_id == period.id,
            PayrollEntry.transaction_id.is_(None),
        )
        if payload.entry_ids:
            q = q.filter(PayrollEntry.id.in_(payload.entry_ids))
        entries = q.all()

        result = PayrollExecuteResult(paid=0, pending_approval=0, skipped=0, errors=[])
        now = datetime.utcnow()
        month_str = f"{period.year}-{period.month:02d}"

        for entry in entries:
            if entry.cash_amount <= 0:
                result.skipped += 1
                continue

            emp = self.db.query(Employee).filter(Employee.id == entry.employee_id).first()
            if not emp:
                result.errors.append(f"Entry {entry.id}: empleado no encontrado")
                continue

            try:
                tx = create_transaction(
                    self.db,
                    session=session,
                    user_id=user.id,
                    delegacion=period.delegacion,
                    category_id=NOMINA_CATEGORY_ID,
                    subcategory_id=NOMINA_SUBCATEGORY_ID,
                    type_="expense",
                    amount=entry.cash_amount,
                    concept=f"Nómina {month_str} — {emp.full_name}",
                    employee_id=emp.id,
                    project_id=NOMINA_PROJECT_ID,
                    work_id=NOMINA_WORK_ID,
                )
                entry.transaction_id = tx.id
                entry.paid_at = now

                if tx.approval_status == "pending_approval":
                    result.pending_approval += 1
                else:
                    result.paid += 1
            except Exception as e:
                result.errors.append(f"Entry {entry.id} ({emp.full_name}): {str(e)[:120]}")

        self.db.add(AuditLog(
            user_id=user.id, delegacion=period.delegacion,
            action="PAYROLL_EXECUTE", entity="payroll_period",
            entity_id=period.id,
            details={"paid": result.paid, "pending": result.pending_approval, "errors": len(result.errors)},
        ))
        self.db.commit()
        return result

    # ── 6. Cerrar periodo ──────────────────────────────────────────────────
    def close_period(self, period_id: int, user: User) -> PayrollPeriod:
        if user.role not in ("admin", "contable"):
            raise HTTPException(status_code=403, detail="Solo admin o contable pueden cerrar periodos")

        period = self._get_or_404(period_id)
        if period.status != "draft":
            raise HTTPException(status_code=400, detail=f"Periodo ya cerrado (status='{period.status}')")

        # Verificar que no quedan entries con cash_amount > 0 sin transaction_id
        unpaid = self.db.query(PayrollEntry).filter(
            PayrollEntry.period_id == period.id,
            PayrollEntry.cash_amount > 0,
            PayrollEntry.transaction_id.is_(None),
        ).count()
        if unpaid > 0:
            raise HTTPException(status_code=400, detail=f"Quedan {unpaid} entradas sin pagar")

        period.status = "paid"
        period.paid_at = datetime.utcnow()
        self.db.add(AuditLog(
            user_id=user.id, delegacion=period.delegacion,
            action="PAYROLL_PERIOD_CLOSED", entity="payroll_period",
            entity_id=period.id, details={},
        ))
        self.db.commit()
        self.db.refresh(period)
        return period

    # ── Helpers ────────────────────────────────────────────────────────────
    def delete_period(self, period_id: int, user) -> dict:
        """Borra fisicamente un periodo de nomina. HERRAMIENTA DE DESARROLLO.
        Restricciones: ENV=development, rol admin/contable, ventana 30 min desde
        creacion. Aborta si algun pago esta en sesion de caja cerrada. Revierte
        anticipos/prestamos/retenciones y elimina transacciones de sesiones abiertas.
        """
        import os
        from datetime import timedelta
        from sqlalchemy import text as _t

        if os.environ.get("ENV", "production") != "development":
            raise HTTPException(status_code=403, detail="El borrado de nominas solo esta disponible en desarrollo")
        if user.role not in ("admin", "contable"):
            raise HTTPException(status_code=403, detail="Solo admin o contable pueden borrar nominas")

        period = self._get_or_404(period_id)
        if datetime.utcnow() - period.created_at > timedelta(minutes=30):
            raise HTTPException(status_code=400, detail="Ventana de borrado de 30 minutos expirada")

        entries = self.db.query(PayrollEntry).filter(PayrollEntry.period_id == period.id).all()

        for e in entries:
            if e.transaction_id:
                row = self.db.execute(_t(
                    "SELECT s.status FROM cash_sessions s "
                    "JOIN transactions t ON t.session_id = s.id WHERE t.id = :tid"
                ), {"tid": e.transaction_id}).fetchone()
                if row and row[0] != "open":
                    raise HTTPException(status_code=400, detail="Hay pagos en una sesion de caja ya cerrada; no se puede borrar")

        reverted = {"advances": 0, "loans": 0, "retentions": 0, "transactions": 0}
        txn_ids = []
        for e in entries:
            refs = e.deduction_refs or {}
            if e.transaction_id or e.liquidated_without_cash:
                for adv in (refs.get("advances") or []):
                    self.db.execute(_t(
                        "UPDATE advances_loans SET amount_repaid = GREATEST(COALESCE(amount_repaid,0) - :amt, 0), "
                        "status = CASE WHEN COALESCE(amount_repaid,0) - :amt <= 0 THEN 'open' ELSE 'partial' END, "
                        "closed_at = NULL WHERE id = :aid"
                    ), {"amt": Decimal(adv["amount"]), "aid": adv["advance_id"]})
                    reverted["advances"] += 1
                for loan in (refs.get("loans") or []):
                    self.db.execute(_t(
                        "UPDATE advances_loans SET amount_repaid = GREATEST(COALESCE(amount_repaid,0) - :amt, 0), "
                        "status = CASE WHEN COALESCE(amount_repaid,0) - :amt <= 0 THEN 'open' ELSE 'partial' END, "
                        "closed_at = NULL WHERE id = :aid"
                    ), {"amt": Decimal(loan["amount"]), "aid": loan["loan_id"]})
                    reverted["loans"] += 1
                for ret in (refs.get("retentions") or []):
                    self.db.execute(_t(
                        "UPDATE retentions_deposits SET status='pending', released_at=NULL, "
                        "release_transaction_id=NULL WHERE id = :rid"
                    ), {"rid": ret["retention_id"]})
                    reverted["retentions"] += 1
            if e.transaction_id:
                txn_ids.append(e.transaction_id)

        self.db.query(PayrollEntry).filter(PayrollEntry.period_id == period.id).delete(synchronize_session=False)

        for tid in txn_ids:
            for tbl in ("transaction_signatures", "transaction_projects", "transaction_attachments", "expense_approvals"):
                self.db.execute(_t("DELETE FROM " + tbl + " WHERE transaction_id = :tid"), {"tid": tid})
            self.db.execute(_t("DELETE FROM transactions WHERE id = :tid"), {"tid": tid})
            reverted["transactions"] += 1

        deleg = period.delegacion
        pid = period.id
        self.db.delete(period)
        self.db.add(AuditLog(
            user_id=user.id, delegacion=deleg, action="PAYROLL_PERIOD_DELETED",
            entity="payroll_period", entity_id=pid,
            details={"reverted": reverted, "entries": len(entries)},
        ))
        self.db.commit()
        return {"deleted": True, "period_id": pid, "reverted": reverted}

    def _get_or_404(self, period_id: int) -> PayrollPeriod:
        p = self.db.query(PayrollPeriod).filter(PayrollPeriod.id == period_id).first()
        if not p:
            raise HTTPException(status_code=404, detail=f"Periodo {period_id} no encontrado")
        return p

    def _enrich_period(self, p: PayrollPeriod) -> dict:
        entries = self.db.query(PayrollEntry).filter(PayrollEntry.period_id == p.id).all()
        creator = self.db.query(User).filter(User.id == p.created_by).first()
        total_cash = sum(Decimal(e.cash_amount) for e in entries)
        paid = sum(1 for e in entries if e.transaction_id is not None)
        pending = sum(1 for e in entries if e.transaction_id is None and e.cash_amount > 0)
        return {
            "id": p.id, "year": p.year, "month": p.month, "delegacion": p.delegacion,
            "status": p.status, "created_by": p.created_by,
            "created_by_name": creator.full_name if creator else None,
            "created_at": p.created_at, "paid_at": p.paid_at, "notes": p.notes,
            "total_employees": len(entries),
            "total_cash": float(total_cash),
            "paid_count": paid, "pending_count": pending,
        }

    def _enrich_entry(self, e: PayrollEntry) -> dict:
        emp = self.db.query(Employee).filter(Employee.id == e.employee_id).first()
        tx_status, tx_ref = None, None
        if e.transaction_id:
            tx = self.db.query(Transaction).filter(Transaction.id == e.transaction_id).first()
            if tx:
                tx_status = tx.approval_status
                tx_ref = tx.reference_number
        return {
            "id": e.id, "employee_id": e.employee_id,
            "employee_name": emp.full_name if emp else None,
            "employee_code": emp.code if emp else None,
            "salary_gross": float(e.salary_gross),
            "salary_transfer": float(e.salary_transfer),
            "cash_amount": float(e.cash_amount),
            "transaction_id": e.transaction_id,
            "transaction_status": tx_status,
            "transaction_reference": tx_ref,
            "paid_at": e.paid_at, "notes": e.notes,
            "deduction_advances": float(e.deduction_advances or 0),
            "deduction_loans": float(e.deduction_loans or 0),
            "deduction_retentions": float(e.deduction_retentions or 0),
            "deduction_refs": e.deduction_refs,
            "manual_override": bool(e.manual_override),
            "liquidated_without_cash": bool(e.liquidated_without_cash),
            "liquidated_at": e.liquidated_at.isoformat() if e.liquidated_at else None,
            "liquidated_by": e.liquidated_by,
        }

    # ── 6. Liquidar deducciones sin movimiento de caja (M10b-v3) ───────────
    def liquidate_without_cash(self, period_id: int, entry_id: int, user: User) -> dict:
        """Liquida deducciones de un entry SIN crear Transaction en caja.
        Aplicable solo a entries con cash_amount=0 y deducciones>0
        (caso deudor neto cronico). Solo gestor de la delegacion.
        """
        period = self._get_or_404(period_id)
        if period.status != "draft":
            raise HTTPException(status_code=400, detail=f"Periodo no editable (status='{period.status}')")
        if user.role != "gestor":
            raise HTTPException(status_code=403, detail="Solo el gestor puede liquidar")
        if period.delegacion != user.delegacion:
            raise HTTPException(status_code=403, detail="Sin acceso a esta delegacion")

        entry = self.db.query(PayrollEntry).filter(
            PayrollEntry.id == entry_id,
            PayrollEntry.period_id == period.id,
        ).first()
        if not entry:
            raise HTTPException(status_code=404, detail="Entry no encontrado")
        if entry.transaction_id:
            raise HTTPException(status_code=400, detail="Entry ya pagada")
        if entry.liquidated_without_cash:
            raise HTTPException(status_code=400, detail="Entry ya liquidada sin caja")
        if Decimal(entry.cash_amount or 0) > 0:
            raise HTTPException(status_code=400, detail="Hay efectivo a pagar: use el flujo de pago normal")

        total_deducc = (
            Decimal(entry.deduction_advances or 0) +
            Decimal(entry.deduction_loans or 0) +
            Decimal(entry.deduction_retentions or 0)
        )
        if total_deducc <= 0:
            raise HTTPException(status_code=400, detail="No hay deducciones que liquidar")

        # Aplicar liquidaciones: advances + loans via repay_by_payroll
        from app.services import advances_service
        refs = entry.deduction_refs or {}

        applied = {"advances": [], "loans": [], "retentions": []}
        for adv in (refs.get("advances") or []):
            amt = Decimal(adv.get("amount", 0))
            if amt <= 0:
                continue
            try:
                advances_service.repay_by_payroll(
                    self.db, adv["advance_id"], AdvanceLoanRepayByPayroll(amount=amt), user.id
                )
                applied["advances"].append({"advance_id": adv["advance_id"], "amount": float(amt)})
            except Exception as e:
                self.db.add(AuditLog(
                    user_id=user.id, delegacion=period.delegacion,
                    action="PAYROLL_LIQUIDATE_NOCASH_ADVANCE_ERROR",
                    entity="advance_loan", entity_id=adv["advance_id"],
                    details={"entry_id": entry.id, "error": str(e)},
                ))

        for loan in (refs.get("loans") or []):
            amt = Decimal(loan.get("amount", 0))
            if amt <= 0:
                continue
            try:
                advances_service.repay_by_payroll(
                    self.db, loan["loan_id"], AdvanceLoanRepayByPayroll(amount=amt), user.id
                )
                applied["loans"].append({"loan_id": loan["loan_id"], "amount": float(amt)})
            except Exception as e:
                self.db.add(AuditLog(
                    user_id=user.id, delegacion=period.delegacion,
                    action="PAYROLL_LIQUIDATE_NOCASH_LOAN_ERROR",
                    entity="advance_loan", entity_id=loan["loan_id"],
                    details={"entry_id": entry.id, "error": str(e)},
                ))

        for ret in (refs.get("retentions") or []):
            amt = Decimal(ret.get("amount", 0))
            if amt <= 0:
                continue
            try:
                rd = self.db.query(RetentionDeposit).filter(RetentionDeposit.id == ret["retention_id"]).first()
                if rd and rd.status == "pending":
                    rd.status = "released"
                    rd.release_date = datetime.utcnow().date()
                    applied["retentions"].append({"retention_id": ret["retention_id"], "amount": float(amt)})
            except Exception as e:
                self.db.add(AuditLog(
                    user_id=user.id, delegacion=period.delegacion,
                    action="PAYROLL_LIQUIDATE_NOCASH_RETENTION_ERROR",
                    entity="retention_deposit", entity_id=ret["retention_id"],
                    details={"entry_id": entry.id, "error": str(e)},
                ))

        # Marcar entry como liquidada sin caja
        entry.liquidated_without_cash = True
        entry.liquidated_at = datetime.utcnow()
        entry.liquidated_by = user.id

        self.db.add(AuditLog(
            user_id=user.id, delegacion=period.delegacion,
            action="PAYROLL_LIQUIDATE_NOCASH",
            entity="payroll_entry", entity_id=entry.id,
            details={"employee_id": entry.employee_id, "applied": applied, "total": float(total_deducc)},
        ))
        self.db.commit()
        self.db.refresh(entry)
        return self._enrich_entry(entry)

