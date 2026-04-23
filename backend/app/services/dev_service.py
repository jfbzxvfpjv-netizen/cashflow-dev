"""
Servicio de reset y carga de fixtures para el entorno de desarrollo.
Solo operativo cuando ENV=development. Los métodos borran datos respetando
el orden de foreign keys para evitar errores de integridad.
"""
import os
import shutil
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database import SessionLocal
from app.models.cash_flow import (
    Transaction, TransactionProject, TransactionAttachment,
    TransactionSignature, CashSession, AccountingPeriod,
    BankWithdrawalRequest
)
from app.models.approvals import ExpenseApproval, CashCount
from app.models.import_history import ImportHistory
from app.models.audit_log import AuditLog
# M9 — módulos financieros
from app.models.financial_modules import (
    AdvanceLoan, RetentionDeposit,
    Float, FloatJustification,
    InstallmentRecord, InstallmentPayment,
    CurrencyOperation, EurStock,
    PartnerAccountMovement,
    ReimbursableExpense,
    MoneyTransfer,
)


class DevService:
    """Operaciones de reset y fixtures exclusivas del entorno de desarrollo."""

    UPLOADS_DIR = "/app/uploads"

    @staticmethod
    def reset_data(db: Session) -> dict:
        """
        Borra transacciones, sesiones, adjuntos, firmas, aprobaciones e historial
        de importación. Conserva catálogos, usuarios y configuración del sistema.
        El orden de borrado respeta las foreign keys.
        """
        counts = {}

        # 1. Módulos M9 (hijos primero — todos referencian Transaction o entre sí)
        counts["installment_payments"] = db.query(InstallmentPayment).delete()
        counts["installment_records"] = db.query(InstallmentRecord).delete()

        counts["float_justifications"] = db.query(FloatJustification).delete()
        counts["floats"] = db.query(Float).delete()

        counts["advances_loans"] = db.query(AdvanceLoan).delete()
        counts["retentions_deposits"] = db.query(RetentionDeposit).delete()

        counts["currency_operations"] = db.query(CurrencyOperation).delete()
        counts["eur_stock"] = db.query(EurStock).delete()

        counts["money_transfers"] = db.query(MoneyTransfer).delete()
        counts["reimbursable_expenses"] = db.query(ReimbursableExpense).delete()
        counts["partner_account_movements"] = db.query(PartnerAccountMovement).delete()

        # 2. Auxiliares de Transaction
        counts["transaction_projects"] = db.query(TransactionProject).delete()
        counts["transaction_signatures"] = db.query(TransactionSignature).delete()
        counts["transaction_attachments"] = db.query(TransactionAttachment).delete()

        # 3. Aprobaciones y arqueos
        counts["expense_approvals"] = db.query(ExpenseApproval).delete()
        counts["cash_counts"] = db.query(CashCount).delete()

        # 4. Historial de importación (referencia cash_sessions)
        counts["import_history"] = db.query(ImportHistory).delete()

        # 5. Transacciones
        counts["transactions"] = db.query(Transaction).delete()

        # 6. Bank withdrawal requests (pueden referenciar sesiones)
        counts["bank_withdrawal_requests"] = db.query(BankWithdrawalRequest).delete()

        # 7. Sesiones de caja
        counts["cash_sessions"] = db.query(CashSession).delete()

        # 8. Auditoría (limpieza total al resetear)
        counts["audit_log"] = db.query(AuditLog).delete()

        # 9. Períodos contables
        counts["accounting_periods"] = db.query(AccountingPeriod).delete()

        # 6. Limpiar ficheros de adjuntos del disco
        if os.path.exists(DevService.UPLOADS_DIR):
            for item in os.listdir(DevService.UPLOADS_DIR):
                item_path = os.path.join(DevService.UPLOADS_DIR, item)
                if os.path.isfile(item_path):
                    os.remove(item_path)
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)

        db.commit()

        return {
            "action": "reset-data",
            "message": "Datos de transacciones borrados. Catálogos y usuarios conservados.",
            "details": counts
        }

    @staticmethod
    def reset_full(db: Session) -> dict:
        """
        Borra TODO el contenido de la base de datos y re-ejecuta seed.py
        para restaurar catálogos, usuarios y configuración inicial.
        """
        # Primero reset de datos
        DevService.reset_data(db)

        # Borrar catálogos y usuarios con TRUNCATE CASCADE
        db.execute(text("""
            TRUNCATE TABLE
                audit_log,
                vehicles, corporate_accounts,
                partners, employees, suppliers,
                transaction_subcategories, transaction_categories,
                works, projects,
                system_config, users
            CASCADE
        """))
        db.commit()

        # Re-ejecutar seed
        from app.seed import run_seed
        seed_db = SessionLocal()
        try:
            run_seed()
        finally:
            seed_db.close()

        return {
            "action": "reset-full",
            "message": "Base de datos reseteada y seed re-ejecutado.",
            "details": {}
        }

    @staticmethod
    def load_fixture(db: Session, nombre: str, user_id: int) -> dict:
        """
        Carga un conjunto de datos de prueba predefinido.
        Primero ejecuta reset_data para partir de un estado limpio.
        """
        # Limpiar datos existentes
        DevService.reset_data(db)

        from app.models.catalogs import (
            Project, Work, TransactionCategory, TransactionSubcategory
        )
        from app.services.integrity_service import compute_transaction_hash

        now = datetime.utcnow()

        if nombre == "basico":
            return DevService._load_basico(db, user_id, now)
        elif nombre == "completo":
            return DevService._load_completo(db, user_id, now)
        elif nombre == "importacion":
            return DevService._load_importacion(db, user_id, now)
        else:
            raise ValueError(f"Fixture '{nombre}' no reconocido. Disponibles: basico, completo, importacion")

    @staticmethod
    def _load_basico(db: Session, user_id: int, now: datetime) -> dict:
        """Fixture básico: 1 sesión con 10 transacciones sencillas."""
        from app.models.catalogs import TransactionCategory, TransactionSubcategory, Project, Work
        from app.services.integrity_service import compute_transaction_hash

        cat = db.query(TransactionCategory).first()
        sub = db.query(TransactionSubcategory).filter_by(category_id=cat.id).first()
        proj = db.query(Project).first()
        work = db.query(Work).filter_by(project_id=proj.id).first()

        session = CashSession(
            user_id=user_id, delegacion="Bata",
            opened_at=now, opening_balance=0, status="open"
        )
        db.add(session)
        db.flush()

        for i in range(1, 11):
            tx = Transaction(
                session_id=session.id, delegacion="Bata",
                category_id=cat.id, subcategory_id=sub.id,
                user_id=user_id,
                counterparty_free=f"Proveedor Test {i}",
                type="expense" if i % 2 == 0 else "income",
                amount=10000 * i,
                concept=f"Transacción de prueba {i}",
                reference_number=f"B{i:04d}",
                transaction_type="normal",
                approval_status="approved",
                editable_until=now + timedelta(minutes=15),
                integrity_hash="pending",
                created_at=now
            )
            db.add(tx)
            db.flush()
            tx.integrity_hash = compute_transaction_hash(tx)

            tp = TransactionProject(
                transaction_id=tx.id, project_id=proj.id, work_id=work.id
            )
            db.add(tp)

        db.commit()
        return {
            "action": "load-fixture",
            "message": "Fixture 'basico' cargado: 1 sesión, 10 transacciones.",
            "details": {"fixture": "basico", "transactions": 10}
        }

    @staticmethod
    def _load_completo(db: Session, user_id: int, now: datetime) -> dict:
        """Fixture completo: 2 sesiones con 50 transacciones variadas."""
        from app.models.catalogs import TransactionCategory, TransactionSubcategory, Project, Work
        from app.services.integrity_service import compute_transaction_hash

        cats = db.query(TransactionCategory).limit(5).all()
        proj = db.query(Project).first()
        work = db.query(Work).filter_by(project_id=proj.id).first()

        total_txns = 0
        for s_idx in range(2):
            deleg = "Bata" if s_idx == 0 else "Malabo"
            prefix = "B" if s_idx == 0 else "M"
            session = CashSession(
                user_id=user_id, delegacion=deleg,
                opened_at=now, opening_balance=0, status="open"
            )
            db.add(session)
            db.flush()

            for i in range(1, 26):
                cat = cats[i % len(cats)]
                sub = db.query(TransactionSubcategory).filter_by(category_id=cat.id).first()
                if not sub:
                    continue
                tx = Transaction(
                    session_id=session.id, delegacion=deleg,
                    category_id=cat.id, subcategory_id=sub.id,
                    user_id=user_id,
                    counterparty_free=f"Contraparte {deleg} {i}",
                    type="expense" if i % 3 != 0 else "income",
                    amount=5000 * i,
                    concept=f"Transacción variada {deleg} {i}",
                    reference_number=f"{prefix}{i:04d}",
                    transaction_type="normal",
                    approval_status="approved",
                    editable_until=now + timedelta(minutes=15),
                    integrity_hash="pending",
                    created_at=now
                )
                db.add(tx)
                db.flush()
                tx.integrity_hash = compute_transaction_hash(tx)

                tp = TransactionProject(
                    transaction_id=tx.id, project_id=proj.id, work_id=work.id
                )
                db.add(tp)
                total_txns += 1

        db.commit()
        return {
            "action": "load-fixture",
            "message": f"Fixture 'completo' cargado: 2 sesiones, {total_txns} transacciones.",
            "details": {"fixture": "completo", "transactions": total_txns}
        }

    @staticmethod
    def _load_importacion(db: Session, user_id: int, now: datetime) -> dict:
        """Fixture de importación: simula datos importados con flags correspondientes."""
        from app.models.catalogs import TransactionCategory, TransactionSubcategory, Project, Work
        from app.services.integrity_service import compute_transaction_hash
        from app.config import settings

        import_edit_days = int(getattr(settings, 'IMPORT_EDIT_DAYS', 30))

        cat = db.query(TransactionCategory).first()
        sub = db.query(TransactionSubcategory).filter_by(category_id=cat.id).first()
        proj = db.query(Project).first()
        work = db.query(Work).filter_by(project_id=proj.id).first()

        session = CashSession(
            user_id=user_id, delegacion="Bata",
            opened_at=now, closed_at=now,
            opening_balance=0, closing_balance=0,
            status="closed",
            notes="[IMPORT] fixture_importacion.xlsx"
        )
        db.add(session)
        db.flush()

        for i in range(1, 21):
            tx = Transaction(
                session_id=session.id, delegacion="Bata",
                category_id=cat.id, subcategory_id=sub.id,
                user_id=user_id,
                counterparty_free=f"Importado Proveedor {i}",
                type="expense" if i % 2 == 0 else "income",
                amount=15000 * i,
                concept=f"Registro importado de prueba {i}",
                reference_number=f"B{i:04d}",
                transaction_type="normal",
                imported=True,
                import_source="fixture_importacion.xlsx",
                imported_editable_until=now + timedelta(days=import_edit_days),
                editable_until=now,
                approval_status="approved",
                integrity_hash="pending",
                created_at=now - timedelta(days=60 - i)
            )
            db.add(tx)
            db.flush()
            tx.integrity_hash = compute_transaction_hash(tx)

            tp = TransactionProject(
                transaction_id=tx.id, project_id=proj.id, work_id=work.id
            )
            db.add(tp)

        # Registrar en historial
        history = ImportHistory(
            delegacion="Bata",
            filename="fixture_importacion.xlsx",
            session_id=session.id,
            rows_imported=20, rows_skipped=0,
            projects_created=0, works_created=0,
            imported_by=user_id
        )
        db.add(history)

        db.commit()
        return {
            "action": "load-fixture",
            "message": "Fixture 'importacion' cargado: 20 transacciones importadas.",
            "details": {"fixture": "importacion", "transactions": 20}
        }
