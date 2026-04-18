"""Utilidades compartidas por los módulos financieros (M9) — v2.

Cambios respecto a v1:
  - get_active_session: lógica 1a+1b. Primero busca sesión propia del usuario;
    si no existe, busca cualquier sesión abierta en su delegación. Flag
    fallback_to_delegation=False fuerza 1a estricto.
  - create_transaction: consulta category_approval_thresholds y aplica
    approval_status='pending_approval' si el importe iguala o supera el umbral
    configurado para la categoría+delegación. Flag check_approval=False salta
    la comprobación para casos internos.
"""
from datetime import datetime, timedelta
from decimal import Decimal
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import catalogs as m
from app.services.integrity_service import compute_transaction_hash
from app.config import settings


def get_active_session(
    db: Session,
    user_id: int,
    delegacion: str,
    fallback_to_delegation: bool = True,
) -> m.CashSession:
    """Obtiene la sesión de caja activa aplicable al usuario.

    Orden de búsqueda:
      1a) Sesión propia del usuario (user_id coincide) con status='open'.
      1b) Si no existe y fallback_to_delegation=True: cualquier sesión con
          status='open' en la delegación indicada.

    Lanza HTTP 409 si no se encuentra ninguna sesión aplicable.
    """
    # 1a — sesión propia del usuario
    session = (
        db.query(m.CashSession)
        .filter(
            m.CashSession.user_id == user_id,
            m.CashSession.status == "open",
        )
        .first()
    )
    if session:
        return session

    # 1b — fallback a cualquier sesión abierta en la delegación
    if fallback_to_delegation and delegacion:
        session = (
            db.query(m.CashSession)
            .filter(
                m.CashSession.delegacion == delegacion,
                m.CashSession.status == "open",
            )
            .first()
        )
        if session:
            return session

    raise HTTPException(
        status_code=409,
        detail=(
            f"No hay sesión de caja activa en {delegacion}. "
            "Abra una sesión antes de registrar."
        ),
    )


def next_reference_number(db: Session, delegacion: str) -> str:
    """Genera el siguiente número de referencia B#### o M#### con bloqueo."""
    prefix = "B" if delegacion == "Bata" else "M"
    last = (
        db.query(m.Transaction)
        .filter(m.Transaction.reference_number.like(f"{prefix}%"))
        .order_by(m.Transaction.id.desc())
        .with_for_update()
        .first()
    )
    if last and last.reference_number:
        try:
            num = int(last.reference_number[1:]) + 1
        except ValueError:
            num = 1
    else:
        num = 1
    return f"{prefix}{num:04d}"


def _resolve_approval_status(
    db: Session,
    category_id: int,
    delegacion: str,
    amount: Decimal,
) -> str:
    """Consulta category_approval_thresholds y devuelve el approval_status
    correcto. Si existe un umbral para la categoría+delegación y el importe
    lo iguala o supera, devuelve 'pending_approval'. En caso contrario
    devuelve 'approved'.
    """
    # Import lazy para evitar ciclos y tolerar ubicación distinta
    # (la clase vive en app.models.approvals, no en catalogs)
    from app.models.approvals import CategoryApprovalThreshold
    threshold_row = (
        db.query(CategoryApprovalThreshold)
        .filter(
            CategoryApprovalThreshold.category_id == category_id,
            CategoryApprovalThreshold.delegacion == delegacion,
        )
        .first()
    )
    if threshold_row and threshold_row.threshold_amount is not None:
        if Decimal(amount) >= Decimal(threshold_row.threshold_amount):
            return "pending_approval"
    return "approved"


def create_transaction(
    db: Session,
    *,
    session: m.CashSession,
    user_id: int,
    delegacion: str,
    category_id: int,
    subcategory_id: int,
    type_: str,
    amount: Decimal,
    concept: str,
    transaction_type: str = "normal",
    supplier_id: int = None,
    employee_id: int = None,
    partner_id: int = None,
    counterparty_free: str = None,
    project_id: int = None,
    work_id: int = None,
    check_approval: bool = True,
) -> m.Transaction:
    """Crea una transacción nativa con su hash, ventana de edición y
    approval_status resuelto según umbral.

    Si check_approval=False se salta la comprobación de umbral y se fuerza
    approval_status='approved'. Uso exclusivo para casos internos como
    transacciones compensatorias donde la aprobación ya se aplicó a la
    transacción principal asociada.
    """
    now = datetime.utcnow()
    editable_until = now + timedelta(
        minutes=getattr(settings, "EDIT_WINDOW_MINUTES", 15)
    )
    ref = next_reference_number(db, delegacion)

    # Resolver approval_status según umbral configurado (o saltar si procede)
    if check_approval:
        approval_status = _resolve_approval_status(
            db, category_id=category_id, delegacion=delegacion, amount=amount
        )
    else:
        approval_status = "approved"

    tx = m.Transaction(
        session_id=session.id,
        delegacion=delegacion,
        category_id=category_id,
        subcategory_id=subcategory_id,
        user_id=user_id,
        type=type_,
        amount=amount,
        concept=concept,
        reference_number=ref,
        transaction_type=transaction_type,
        supplier_id=supplier_id,
        employee_id=employee_id,
        partner_id=partner_id,
        counterparty_free=counterparty_free,
        editable_until=editable_until,
        integrity_hash="pending",
        approval_status=approval_status,
        created_at=now,
    )
    db.add(tx)
    db.flush()
    tx.integrity_hash = compute_transaction_hash(tx)

    if project_id and work_id:
        db.add(
            m.TransactionProject(
                transaction_id=tx.id,
                project_id=project_id,
                work_id=work_id,
            )
        )
    db.flush()
    return tx
