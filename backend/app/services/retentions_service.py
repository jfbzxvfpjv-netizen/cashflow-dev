"""Retenciones y depósitos — M9 Fase 1 Parte C.

Interpretación C mixta:
  - type='deposit' (fianza entregada a tercero): el dinero sale físicamente
    de caja al crear. create_transaction egreso. Al liberar vuelve el dinero:
    create_transaction ingreso.
  - type='retention' (dinero retenido en caja): al crear NO hay movimiento
    físico, solo registro. Al liberar el dinero sale al destinatario final:
    create_transaction egreso.

Vinculación:
  - creation_transaction_id: solo para deposit.
  - release_transaction_id: ambos tipos al liberar.
"""
from decimal import Decimal
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import catalogs as m
from app.services.financial_helpers import get_active_session, create_transaction


def _to_out(db: Session, it: m.RetentionDeposit) -> dict:
    sup = (
        db.query(m.Supplier).filter(m.Supplier.id == it.supplier_id).first()
        if it.supplier_id else None
    )
    emp = (
        db.query(m.Employee).filter(m.Employee.id == it.employee_id).first()
        if it.employee_id else None
    )
    return {
        "id": it.id,
        "type": it.type,
        "amount": it.amount,
        "concept": it.concept,
        "status": it.status,
        "release_date": it.release_date,
        "released_at": it.released_at,
        "supplier_id": it.supplier_id,
        "employee_id": it.employee_id,
        "supplier_name": sup.name if sup else None,
        "employee_name": emp.full_name if emp else None,
        "creation_transaction_id": getattr(it, "creation_transaction_id", None),
        "release_transaction_id": getattr(it, "release_transaction_id", None),
    }


def list_all(db: Session, status: str = None, type_: str = None):
    q = db.query(m.RetentionDeposit)
    if status:
        q = q.filter(m.RetentionDeposit.status == status)
    if type_:
        q = q.filter(m.RetentionDeposit.type == type_)
    items = q.order_by(m.RetentionDeposit.id.desc()).all()
    return [_to_out(db, it) for it in items]


def _counterparty_name(db: Session, data) -> str:
    """Devuelve un string descriptivo de proveedor o empleado para el concept."""
    if data.supplier_id:
        sup = db.query(m.Supplier).filter(m.Supplier.id == data.supplier_id).first()
        return sup.name if sup else "Proveedor"
    if data.employee_id:
        emp = db.query(m.Employee).filter(m.Employee.id == data.employee_id).first()
        return emp.full_name if emp else "Empleado"
    return "Tercero"


def create(db: Session, data, user, delegacion: str):
    """Crea un registro de retención o depósito.

    Para deposit: crea transacción egreso en caja y guarda el ID.
    Para retention: solo inserta el registro (no hay movimiento físico).
    """
    if not data.supplier_id and not data.employee_id:
        raise HTTPException(status_code=400, detail="Indique proveedor o empleado")

    creation_tx_id = None

    if data.type == "deposit":
        # Validar campos obligatorios para crear la transacción
        missing = [
            f for f in ("category_id", "subcategory_id", "project_id", "work_id")
            if getattr(data, f, None) is None
        ]
        if missing:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Para depósitos es obligatorio indicar "
                    f"{', '.join(missing)} — el dinero sale de caja al entregarlo."
                ),
            )

        session = get_active_session(db, user.id, delegacion)
        cp_name = _counterparty_name(db, data)

        tx = create_transaction(
            db,
            session=session,
            user_id=user.id,
            delegacion=delegacion,
            category_id=data.category_id,
            subcategory_id=data.subcategory_id,
            type_="expense",
            amount=data.amount,
            concept=f"[Depósito a {cp_name}] {data.concept}",
            transaction_type="deposit",
            supplier_id=data.supplier_id,
            employee_id=data.employee_id,
            project_id=data.project_id,
            work_id=data.work_id,
        )
        creation_tx_id = tx.id

    # Insertar el registro (con o sin transacción asociada según tipo)
    item = m.RetentionDeposit(
        type=data.type,
        amount=data.amount,
        concept=data.concept,
        supplier_id=data.supplier_id,
        employee_id=data.employee_id,
        release_date=data.release_date,
        status="pending",
        creation_transaction_id=creation_tx_id,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return _to_out(db, item)


def release(db: Session, item_id: int, data, user, delegacion: str):
    """Libera un registro. Siempre crea transacción en caja:
      - deposit: transacción INGRESO (vuelve el dinero del tercero).
      - retention: transacción EGRESO (sale el dinero al destinatario).
    """
    item = db.query(m.RetentionDeposit).filter(m.RetentionDeposit.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Retención/depósito no encontrado")
    if item.status == "released":
        raise HTTPException(status_code=400, detail="Ya liberado")

    session = get_active_session(db, user.id, delegacion)

    # Determinar quién es el "destinatario" para el concept
    sup = (
        db.query(m.Supplier).filter(m.Supplier.id == item.supplier_id).first()
        if item.supplier_id else None
    )
    emp = (
        db.query(m.Employee).filter(m.Employee.id == item.employee_id).first()
        if item.employee_id else None
    )
    cp_name = sup.name if sup else (emp.full_name if emp else "Tercero")

    concept_suffix = data.concept if data.concept else item.concept

    if item.type == "deposit":
        # Vuelve el dinero del tercero -> INGRESO
        tx_type_flow = "income"
        concept_prefix = f"[Devolución de depósito por {cp_name}]"
    else:
        # type == 'retention' — sale el dinero retenido al destinatario -> EGRESO
        tx_type_flow = "expense"
        concept_prefix = f"[Liberación de retención a {cp_name}]"

    tx = create_transaction(
        db,
        session=session,
        user_id=user.id,
        delegacion=delegacion,
        category_id=data.category_id,
        subcategory_id=data.subcategory_id,
        type_=tx_type_flow,
        amount=item.amount,
        concept=f"{concept_prefix} {concept_suffix}",
        transaction_type=item.type,  # 'deposit' o 'retention'
        supplier_id=item.supplier_id,
        employee_id=item.employee_id,
        project_id=data.project_id,
        work_id=data.work_id,
    )

    item.status = "released"
    item.released_at = datetime.utcnow()
    item.release_transaction_id = tx.id

    db.commit()
    db.refresh(item)
    return _to_out(db, item)
