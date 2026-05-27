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
from app.models.cash_flow import Transaction
from app.models.user import User
from app.models.audit_log import AuditLog
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

    # ── 1. Generar periodo ─────────────────────────────────────────────────
    def generate_period(self, data: PayrollPeriodCreate, user: User) -> PayrollPeriod:
        if user.role != "admin":
            raise HTTPException(status_code=403, detail="Solo admin puede generar periodos de nómina")

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
            cash = max(gross - transfer, Decimal(0))
            entry = PayrollEntry(
                period_id=period.id,
                employee_id=emp.id,
                salary_gross=gross,
                salary_transfer=transfer,
                cash_amount=cash,
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
        if user.role != "admin":
            raise HTTPException(status_code=403, detail="Solo admin puede editar entradas de nómina")

        entry = self.db.query(PayrollEntry).filter(PayrollEntry.id == entry_id).first()
        if not entry:
            raise HTTPException(status_code=404, detail="Entrada no encontrada")
        period = self._get_or_404(entry.period_id)
        if period.status != "draft":
            raise HTTPException(status_code=400, detail=f"Periodo no editable (status='{period.status}')")
        if entry.transaction_id:
            raise HTTPException(status_code=400, detail="No se puede editar: entrada ya pagada")

        if data.cash_amount is not None:
            entry.cash_amount = data.cash_amount
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
        if user.role != "admin":
            raise HTTPException(status_code=403, detail="Solo admin puede cerrar periodos")

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
        }
