"""Anticipos y préstamos a empleados — ciclo open/partial/closed.

M9 Fase 1: create y repay manual crean transacciones en caja. Nuevo endpoint
repay-by-payroll (uso interno desde el service de nómina) solo marca el
anticipo como saldado sin tocar caja — porque en ese caso la transacción
de caja es la del pago de nómina reducido.
"""
from decimal import Decimal
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import update

from app.models import catalogs as m
from app.services.financial_helpers import get_active_session, create_transaction


def _to_out(db: Session, it: m.AdvanceLoan) -> dict:
    """Serializa un AdvanceLoan con los campos calculados del schema Out."""
    emp = db.query(m.Employee).filter(m.Employee.id == it.employee_id).first()
    amount = it.amount or Decimal("0")
    repaid = it.amount_repaid or Decimal("0")
    return {
        "id": it.id,
        "employee_id": it.employee_id,
        "employee_name": emp.full_name if emp else None,
        "type": it.type,
        "amount": amount,
        "concept": it.concept,
        "status": it.status,
        "amount_repaid": repaid,
        "pending": amount - repaid,
        "opened_at": it.opened_at,
        "closed_at": it.closed_at,
        "creation_transaction_id": getattr(it, "creation_transaction_id", None),
        "repay_transaction_ids": list(getattr(it, "repay_transaction_ids", None) or []),
    }


def list_all(db: Session, status: str = None, employee_id: int = None):
    q = db.query(m.AdvanceLoan)
    if status:
        q = q.filter(m.AdvanceLoan.status == status)
    if employee_id:
        q = q.filter(m.AdvanceLoan.employee_id == employee_id)
    items = q.order_by(m.AdvanceLoan.opened_at.desc()).all()
    return [_to_out(db, it) for it in items]


def create(db: Session, data, user, delegacion: str):
    """Crea un anticipo/préstamo:
      1. Valida empleado activo.
      2. Obtiene sesión de caja activa (con fallback a delegación).
      3. Crea transacción egreso en caja (transaction_type='advance' o 'loan').
      4. Registra el anticipo con vinculación a la transacción.

    El dinero sale físicamente de caja al entregar el anticipo al empleado,
    por eso se crea la transacción. El ciclo open/partial/closed se gestiona
    independientemente del approval_status de la transacción.
    """
    emp = (
        db.query(m.Employee)
        .filter(m.Employee.id == data.employee_id, m.Employee.active == True)
        .first()
    )
    if not emp:
        raise HTTPException(status_code=404, detail="Empleado no encontrado o inactivo")

    session = get_active_session(db, user.id, delegacion)

    # transaction_type según sea anticipo o préstamo
    tx_type_str = "advance" if data.type == "advance" else "loan"

    tx = create_transaction(
        db,
        session=session,
        user_id=user.id,
        delegacion=delegacion,
        category_id=data.category_id,
        subcategory_id=data.subcategory_id,
        type_="expense",
        amount=data.amount,
        concept=f"[{tx_type_str.capitalize()} a {emp.full_name}] {data.concept}",
        transaction_type=tx_type_str,
        employee_id=emp.id,
        project_id=data.project_id,
        work_id=data.work_id,
    )

    item = m.AdvanceLoan(
        employee_id=data.employee_id,
        type=data.type,
        amount=data.amount,
        concept=data.concept,
        status="open",
        amount_repaid=Decimal("0"),
        opened_at=datetime.utcnow(),
        creation_transaction_id=tx.id,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return _to_out(db, item)


def repay(db: Session, advance_id: int, data, user, delegacion: str):
    """Repay manual — el empleado devuelve dinero en efectivo a caja.

    Crea transacción ingreso y vincula al anticipo mediante repay_transaction_ids.
    Si el total repagado iguala al anticipo, estado pasa a 'closed'.
    """
    item = db.query(m.AdvanceLoan).filter(m.AdvanceLoan.id == advance_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Anticipo no encontrado")
    if item.status == "closed":
        raise HTTPException(status_code=400, detail="El anticipo ya está cerrado")

    amount = Decimal(data.amount)
    new_repaid = (item.amount_repaid or Decimal("0")) + amount
    if new_repaid > item.amount:
        raise HTTPException(
            status_code=400,
            detail="El importe a devolver excede lo adeudado",
        )

    emp = db.query(m.Employee).filter(m.Employee.id == item.employee_id).first()
    session = get_active_session(db, user.id, delegacion)

    concept_suffix = data.concept if data.concept else item.concept
    tx_type_str = "advance" if item.type == "advance" else "loan"

    tx = create_transaction(
        db,
        session=session,
        user_id=user.id,
        delegacion=delegacion,
        category_id=data.category_id,
        subcategory_id=data.subcategory_id,
        type_="income",
        amount=amount,
        concept=f"[Devolución {tx_type_str} de {emp.full_name if emp else 'empleado'}] {concept_suffix}",
        transaction_type=tx_type_str,
        employee_id=item.employee_id,
        project_id=data.project_id,
        work_id=data.work_id,
    )

    # Añadir ID al array de transacciones de repay
    # Nota: PostgreSQL array append vía SQLAlchemy requiere reasignar la lista
    existing_ids = list(item.repay_transaction_ids or [])
    existing_ids.append(tx.id)
    item.repay_transaction_ids = existing_ids

    item.amount_repaid = new_repaid
    if new_repaid == item.amount:
        item.status = "closed"
        item.closed_at = datetime.utcnow()
    else:
        item.status = "partial"

    db.commit()
    db.refresh(item)
    return _to_out(db, item)


def repay_by_payroll(db: Session, advance_id: int, data, user_id: int):
    """Repay automático desde nómina (M10) — NO crea transacción.

    Este endpoint solo debe invocarse internamente desde el service de nómina
    cuando un anticipo se salda por descuento en el salario del empleado.
    En ese caso, la transacción de caja es la del pago de nómina reducido
    (salary_cash - advance_amount), no una transacción de devolución separada.

    Se limita a actualizar amount_repaid y status del anticipo.
    """
    item = db.query(m.AdvanceLoan).filter(m.AdvanceLoan.id == advance_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Anticipo no encontrado")
    if item.status == "closed":
        raise HTTPException(status_code=400, detail="El anticipo ya está cerrado")

    amount = Decimal(data.amount)
    new_repaid = (item.amount_repaid or Decimal("0")) + amount
    if new_repaid > item.amount:
        raise HTTPException(
            status_code=400,
            detail="El importe a devolver excede lo adeudado",
        )

    item.amount_repaid = new_repaid
    if new_repaid == item.amount:
        item.status = "closed"
        item.closed_at = datetime.utcnow()
    else:
        item.status = "partial"

    db.commit()
    db.refresh(item)
    return _to_out(db, item)
