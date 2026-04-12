"""
Módulo 6 — Servicio de negocio para transacciones.
Gestiona la creación con validación completa, la política de inmutabilidad
(ventana de 15 minutos para nativos, 30 días para importados), el cálculo
del hash SHA-256, las cancelaciones mediante contrapartida inversa y el
sistema de aprobaciones por umbral configurable.
"""
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.config import settings
from app.models.cash_flow import (
    Transaction, TransactionProject, TransactionAttachment,
    TransactionSignature, CashSession, AccountingPeriod
)
from app.models.catalogs import (
    TransactionCategory, TransactionSubcategory,
    Project, Work, Supplier, Employee, Partner, Vehicle
)
from app.models.approvals import CategoryApprovalThreshold, ExpenseApproval
from app.models.audit_log import AuditLog
from app.models.user import User
from app.services.integrity_service import compute_transaction_hash
from app.services.reference_service import generate_reference


class TransactionService:
    """Servicio central de transacciones con todas las reglas de negocio."""

    # ── Creación ──────────────────────────────────────────────────────

    @staticmethod
    def create_transaction(db: Session, data: dict, user: User) -> Transaction:
        """
        Crea una transacción nueva validando sesión abierta, relaciones de
        catálogo, contraparte obligatoria, umbral de aprobación y cálculo
        de hash SHA-256.
        """
        # 1. Verificar sesión abierta del usuario
        session = db.query(CashSession).filter(
            CashSession.user_id == user.id,
            CashSession.status == "open"
        ).first()
        if not session:
            raise ValueError("No tiene una sesión de caja abierta")

        delegacion = session.delegacion

        # 2. Verificar que el mes no esté cerrado contablemente
        now = datetime.utcnow()
        period_closed = db.query(AccountingPeriod).filter(
            AccountingPeriod.year == now.year,
            AccountingPeriod.month == now.month,
            AccountingPeriod.delegacion.in_([delegacion, "Ambas"])
        ).first()
        if period_closed:
            raise ValueError(f"El período contable {now.month}/{now.year} está cerrado para {delegacion}")

        # 3. Validar categoría y subcategoría
        category = db.query(TransactionCategory).filter(
            TransactionCategory.id == data["category_id"],
            TransactionCategory.active == True
        ).first()
        if not category:
            raise ValueError("Categoría no encontrada o inactiva")

        if category.type not in (data["type"], "both"):
            raise ValueError(f"La categoría '{category.name}' no admite tipo '{data['type']}'")

        subcat = db.query(TransactionSubcategory).filter(
            TransactionSubcategory.id == data["subcategory_id"],
            TransactionSubcategory.category_id == data["category_id"],
            TransactionSubcategory.active == True
        ).first()
        if not subcat:
            raise ValueError("Subcategoría no encontrada o no pertenece a la categoría seleccionada")

        # 4. Validar proyectos y obras (al menos uno obligatorio)
        projects_data = data.get("projects", [])
        if not projects_data:
            raise ValueError("Debe asignar al menos un proyecto y obra")

        for p in projects_data:
            proj = db.query(Project).filter(Project.id == p["project_id"]).first()
            if not proj:
                raise ValueError(f"Proyecto ID {p['project_id']} no encontrado")
            # Crear obra al vuelo si work_id es negativo (convención frontend)
            if p.get("work_id", 0) < 0:
                raise ValueError("Para crear obras al vuelo use el endpoint de obras")
            work = db.query(Work).filter(
                Work.id == p["work_id"],
                Work.project_id == p["project_id"]
            ).first()
            if not work:
                raise ValueError(f"Obra ID {p['work_id']} no encontrada en proyecto {p['project_id']}")

        # 5. Validar contraparte (al menos una obligatoria)
        has_counterparty = any([
            data.get("supplier_id"),
            data.get("employee_id"),
            data.get("partner_id"),
            data.get("counterparty_free")
        ])
        if not has_counterparty:
            raise ValueError("Debe indicar al menos una contraparte (proveedor, empleado, socio o texto libre)")

        # Validar existencia de entidades referenciadas
        if data.get("supplier_id"):
            if not db.query(Supplier).filter(Supplier.id == data["supplier_id"]).first():
                raise ValueError("Proveedor no encontrado")
        if data.get("employee_id"):
            if not db.query(Employee).filter(Employee.id == data["employee_id"]).first():
                raise ValueError("Empleado no encontrado")
        if data.get("partner_id"):
            if not db.query(Partner).filter(Partner.id == data["partner_id"]).first():
                raise ValueError("Socio no encontrado")
        if data.get("vehicle_id"):
            if not db.query(Vehicle).filter(Vehicle.id == data["vehicle_id"]).first():
                raise ValueError("Vehículo no encontrado")

        # 6. Generar referencia secuencial (B0001 / M0001)
        reference = generate_reference(db, delegacion)

        # 7. Calcular ventana de edición
        edit_minutes = getattr(settings, "EDIT_WINDOW_MINUTES", 15)
        editable_until = now + timedelta(minutes=edit_minutes)

        # 8. Comprobar umbral de aprobación
        approval_status = "approved"
        threshold = db.query(CategoryApprovalThreshold).filter(
            CategoryApprovalThreshold.category_id == data["category_id"],
            CategoryApprovalThreshold.delegacion == delegacion
        ).first()
        if threshold and Decimal(str(data["amount"])) > threshold.threshold_amount:
            approval_status = "pending_approval"

        # 9. Crear la transacción
        txn = Transaction(
            session_id=session.id,
            delegacion=delegacion,
            category_id=data["category_id"],
            subcategory_id=data["subcategory_id"],
            user_id=user.id,
            supplier_id=data.get("supplier_id"),
            employee_id=data.get("employee_id"),
            partner_id=data.get("partner_id"),
            counterparty_free=data.get("counterparty_free"),
            vehicle_id=data.get("vehicle_id"),
            type=data["type"],
            amount=data["amount"],
            concept=data["concept"],
            reference_number=reference,
            transaction_type=data.get("transaction_type", "normal"),
            cancelled=False,
            is_adjustment=False,
            approval_status=approval_status,
            imported=False,
            editable_until=editable_until,
            integrity_hash="pending",
            created_at=now
        )
        db.add(txn)
        db.flush()

        # 10. Asignar proyectos y obras
        for p in projects_data:
            tp = TransactionProject(
                transaction_id=txn.id,
                project_id=p["project_id"],
                work_id=p["work_id"]
            )
            db.add(tp)

        # 11. Calcular hash SHA-256
        txn.integrity_hash = compute_transaction_hash(txn)

        # 12. Registrar aprobación pendiente si aplica
        if approval_status == "pending_approval":
            ea = ExpenseApproval(
                transaction_id=txn.id,
                requested_by=user.id,
                status="pending"
            )
            db.add(ea)

        # 13. Auditoría
        db.add(AuditLog(
            user_id=user.id,
            delegacion=delegacion,
            action="CREATE_TRANSACTION",
            entity="Transaction",
            entity_id=txn.id,
            details={"reference": reference, "amount": str(data["amount"]), "type": data["type"]}
        ))

        db.commit()
        db.refresh(txn)
        return txn

    # ── Actualización dentro de ventana ───────────────────────────────

    @staticmethod
    def update_transaction(db: Session, txn_id: int, data: dict, user: User) -> Transaction:
        """
        Modifica una transacción dentro de su ventana de edición.
        Solo el Administrador puede editar. Recalcula el hash SHA-256.
        """
        txn = db.query(Transaction).filter(Transaction.id == txn_id).first()
        if not txn:
            raise ValueError("Transacción no encontrada")
        if txn.cancelled:
            raise ValueError("No se puede editar una transacción cancelada")

        now = datetime.utcnow()

        # Ventana de edición: nativos 15 min, importados 30 días
        if txn.imported:
            if txn.imported_editable_until and now > txn.imported_editable_until:
                raise PermissionError("La ventana de corrección de 30 días ha expirado")
        else:
            if now > txn.editable_until:
                raise PermissionError(
                    "El período de edición ha expirado. Utilice el mecanismo de anulación."
                )

        # Verificar que la sesión no esté cerrada
        session = db.query(CashSession).filter(CashSession.id == txn.session_id).first()
        if session and session.status == "closed":
            raise ValueError("No se pueden modificar transacciones de una sesión cerrada")

        # Valores anteriores para auditoría
        old_values = {
            "amount": str(txn.amount), "concept": txn.concept,
            "category_id": txn.category_id, "type": txn.type
        }

        # Aplicar cambios
        updatable_fields = [
            "category_id", "subcategory_id", "type", "amount", "concept",
            "supplier_id", "employee_id", "partner_id", "counterparty_free",
            "vehicle_id"
        ]
        for field in updatable_fields:
            if field in data and data[field] is not None:
                setattr(txn, field, data[field])

        # Actualizar proyectos si se proporcionan
        if "projects" in data and data["projects"] is not None:
            db.query(TransactionProject).filter(
                TransactionProject.transaction_id == txn.id
            ).delete()
            for p in data["projects"]:
                db.add(TransactionProject(
                    transaction_id=txn.id,
                    project_id=p["project_id"],
                    work_id=p["work_id"]
                ))

        # Recalcular hash
        txn.integrity_hash = compute_transaction_hash(txn)

        # Auditoría
        new_values = {
            "amount": str(txn.amount), "concept": txn.concept,
            "category_id": txn.category_id, "type": txn.type
        }
        db.add(AuditLog(
            user_id=user.id,
            delegacion=txn.delegacion,
            action="EDIT_IMPORTED_TRANSACTION" if txn.imported else "EDIT_TRANSACTION",
            entity="Transaction",
            entity_id=txn.id,
            details={"old": old_values, "new": new_values}
        ))

        db.commit()
        db.refresh(txn)
        return txn

    # ── Cancelación con contrapartida ─────────────────────────────────

    @staticmethod
    def cancel_transaction(db: Session, txn_id: int, reason: str, user: User) -> Transaction:
        """
        Cancela una transacción generando un asiento de contrapartida inversa
        en la sesión activa del usuario. La transacción original se marca
        como cancelled=True.
        """
        txn = db.query(Transaction).filter(Transaction.id == txn_id).first()
        if not txn:
            raise ValueError("Transacción no encontrada")
        if txn.cancelled:
            raise ValueError("La transacción ya está cancelada")

        # Buscar sesión activa para la contrapartida
        active_session = db.query(CashSession).filter(
            CashSession.user_id == user.id,
            CashSession.status == "open"
        ).first()
        if not active_session:
            raise ValueError("Necesita una sesión abierta para registrar la contrapartida")

        now = datetime.utcnow()
        edit_minutes = getattr(settings, "EDIT_WINDOW_MINUTES", 15)
        counter_ref = generate_reference(db, active_session.delegacion)

        # Tipo inverso para la contrapartida
        counter_type = "expense" if txn.type == "income" else "income"

        # Crear contrapartida
        counter = Transaction(
            session_id=active_session.id,
            delegacion=active_session.delegacion,
            category_id=txn.category_id,
            subcategory_id=txn.subcategory_id,
            user_id=user.id,
            supplier_id=txn.supplier_id,
            employee_id=txn.employee_id,
            partner_id=txn.partner_id,
            counterparty_free=txn.counterparty_free,
            vehicle_id=txn.vehicle_id,
            type=counter_type,
            amount=txn.amount,
            concept=f"[ANULACIÓN de {txn.reference_number}] {reason}",
            reference_number=counter_ref,
            transaction_type="adjustment",
            cancelled=False,
            cancel_ref_id=txn.id,
            is_adjustment=True,
            approval_status="approved",
            imported=False,
            editable_until=now + timedelta(minutes=edit_minutes),
            integrity_hash="pending",
            created_at=now
        )
        db.add(counter)
        db.flush()

        # Copiar asignación de proyectos
        orig_projects = db.query(TransactionProject).filter(
            TransactionProject.transaction_id == txn.id
        ).all()
        for op in orig_projects:
            db.add(TransactionProject(
                transaction_id=counter.id,
                project_id=op.project_id,
                work_id=op.work_id
            ))

        counter.integrity_hash = compute_transaction_hash(counter)

        # Marcar original como cancelada
        txn.cancelled = True
        txn.cancel_ref_id = counter.id

        # Auditoría
        db.add(AuditLog(
            user_id=user.id,
            delegacion=txn.delegacion,
            action="CANCEL_TRANSACTION",
            entity="Transaction",
            entity_id=txn.id,
            details={"reason": reason, "counter_ref": counter_ref, "counter_id": counter.id}
        ))

        db.commit()
        db.refresh(txn)
        return txn

    # ── Aprobación y rechazo ──────────────────────────────────────────

    @staticmethod
    def approve_transaction(db: Session, txn_id: int, user: User) -> Transaction:
        """Admin autoriza la transacción. Queda como 'authorized' hasta que
        el Gestor confirme la ejecución física del pago."""
        txn = db.query(Transaction).filter(Transaction.id == txn_id).first()
        if not txn:
            raise ValueError("Transacción no encontrada")
        if txn.approval_status != "pending_approval":
            raise ValueError("La transacción no está pendiente de aprobación")

        now = datetime.utcnow()
        txn.approval_status = "authorized"
        txn.approved_by = user.id
        txn.approved_at = now

        ea = db.query(ExpenseApproval).filter(
            ExpenseApproval.transaction_id == txn_id,
            ExpenseApproval.status == "pending"
        ).first()
        if ea:
            ea.status = "authorized"
            ea.approved_by = user.id
            ea.approved_at = now

        db.add(AuditLog(
            user_id=user.id,
            delegacion=txn.delegacion,
            action="AUTHORIZE_TRANSACTION",
            entity="Transaction",
            entity_id=txn.id,
            details={"reference": txn.reference_number}
        ))

        db.commit()
        db.refresh(txn)
        return txn

    @staticmethod
    def execute_transaction(db: Session, txn_id: int, user: User) -> Transaction:
        """El Gestor confirma la ejecución física del pago. La transacción
        pasa a 'approved' y computa en el saldo de caja."""
        txn = db.query(Transaction).filter(Transaction.id == txn_id).first()
        if not txn:
            raise ValueError("Transacción no encontrada")
        if txn.approval_status != "authorized":
            raise ValueError("La transacción no está autorizada para ejecución")

        # Verificar que el gestor pertenece a la delegación
        if user.role == "gestor" and txn.delegacion != user.delegacion:
            raise ValueError("Sin acceso a transacciones de otra delegación")

        now = datetime.utcnow()
        txn.approval_status = "approved"

        ea = db.query(ExpenseApproval).filter(
            ExpenseApproval.transaction_id == txn_id,
            ExpenseApproval.status == "authorized"
        ).first()
        if ea:
            ea.status = "approved"

        db.add(AuditLog(
            user_id=user.id,
            delegacion=txn.delegacion,
            action="EXECUTE_TRANSACTION",
            entity="Transaction",
            entity_id=txn.id,
            details={"reference": txn.reference_number, "executed_by": user.username}
        ))

        db.commit()
        db.refresh(txn)
        return txn

    @staticmethod
    def reject_transaction(db: Session, txn_id: int, reason: str, user: User) -> Transaction:
        txn = db.query(Transaction).filter(Transaction.id == txn_id).first()
        if not txn:
            raise ValueError("Transacción no encontrada")
        if txn.approval_status != "pending_approval":
            raise ValueError("La transacción no está pendiente de aprobación")

        txn.approval_status = "rejected"
        txn.approved_by = user.id
        txn.approved_at = datetime.utcnow()

        ea = db.query(ExpenseApproval).filter(
            ExpenseApproval.transaction_id == txn_id,
            ExpenseApproval.status == "pending"
        ).first()
        if ea:
            ea.status = "rejected"
            ea.approved_by = user.id
            ea.approved_at = datetime.utcnow()
            ea.rejection_reason = reason

        db.add(AuditLog(
            user_id=user.id,
            delegacion=txn.delegacion,
            action="REJECT_TRANSACTION",
            entity="Transaction",
            entity_id=txn.id,
            details={"reference": txn.reference_number, "reason": reason}
        ))

        db.commit()
        db.refresh(txn)
        return txn

    # ── Listado con filtros y paginación ──────────────────────────────

    @staticmethod
    def list_transactions(db: Session, filters: dict, user: User) -> dict:
        """
        Lista transacciones con filtros avanzados, paginación y cálculo
        en tiempo real del estado de edición (is_editable, seconds_remaining).
        """
        query = db.query(Transaction)

        # Filtrado por delegación automático para Gestor de Caja
        if user.role == "gestor":
            query = query.filter(Transaction.delegacion == user.delegacion)
        elif filters.get("delegacion"):
            query = query.filter(Transaction.delegacion == filters["delegacion"])

        # Filtros opcionales
        filter_map = {
            "session_id": Transaction.session_id,
            "type": Transaction.type,
            "category_id": Transaction.category_id,
            "subcategory_id": Transaction.subcategory_id,
            "supplier_id": Transaction.supplier_id,
            "employee_id": Transaction.employee_id,
            "partner_id": Transaction.partner_id,
            "vehicle_id": Transaction.vehicle_id,
            "transaction_type": Transaction.transaction_type,
            "approval_status": Transaction.approval_status,
        }
        for key, col in filter_map.items():
            if filters.get(key):
                query = query.filter(col == filters[key])

        if filters.get("imported") is not None:
            query = query.filter(Transaction.imported == filters["imported"])
        if filters.get("cancelled") is not None:
            query = query.filter(Transaction.cancelled == filters["cancelled"])
        if filters.get("date_start"):
            query = query.filter(Transaction.created_at >= filters["date_start"])
        if filters.get("date_end"):
            query = query.filter(Transaction.created_at <= filters["date_end"])
        if filters.get("concept"):
            query = query.filter(Transaction.concept.ilike(f"%{filters['concept']}%"))
        if filters.get("min_amount"):
            query = query.filter(Transaction.amount >= filters["min_amount"])
        if filters.get("max_amount"):
            query = query.filter(Transaction.amount <= filters["max_amount"])
        if filters.get("project_id"):
            query = query.join(TransactionProject).filter(
                TransactionProject.project_id == filters["project_id"]
            )
        if filters.get("work_id"):
            query = query.join(TransactionProject).filter(
                TransactionProject.work_id == filters["work_id"]
            )

        total = query.count()
        page = max(1, filters.get("page", 1))
        page_size = min(100, max(1, filters.get("page_size", 50)))
        pages = max(1, (total + page_size - 1) // page_size)

        items = query.order_by(Transaction.created_at.desc()).offset(
            (page - 1) * page_size
        ).limit(page_size).all()

        return {"items": items, "total": total, "page": page, "page_size": page_size, "pages": pages}

    # ── Detalle ───────────────────────────────────────────────────────

    @staticmethod
    def get_transaction_detail(db: Session, txn_id: int, user: User):
        txn = db.query(Transaction).filter(Transaction.id == txn_id).first()
        if not txn:
            return None
        if user.role == "gestor" and txn.delegacion != user.delegacion:
            return None
        return txn

    # ── Integridad ────────────────────────────────────────────────────

    @staticmethod
    def verify_all_integrity(db: Session) -> dict:
        """Verifica el hash SHA-256 de todas las transacciones."""
        transactions = db.query(Transaction).all()
        total = len(transactions)
        ok = 0
        failures = []
        for txn in transactions:
            expected = compute_transaction_hash(txn)
            if txn.integrity_hash == expected:
                ok += 1
            else:
                failures.append({
                    "id": txn.id,
                    "reference": txn.reference_number,
                    "stored_hash": txn.integrity_hash,
                    "computed_hash": expected
                })
        return {"total": total, "verified_ok": ok, "failures": failures}

    @staticmethod
    def verify_single_integrity(db: Session, txn_id: int) -> dict:
        txn = db.query(Transaction).filter(Transaction.id == txn_id).first()
        if not txn:
            raise ValueError("Transacción no encontrada")
        expected = compute_transaction_hash(txn)
        return {
            "id": txn.id,
            "reference": txn.reference_number,
            "stored_hash": txn.integrity_hash,
            "computed_hash": expected,
            "valid": txn.integrity_hash == expected
        }
