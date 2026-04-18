"""Circulantes — M9 Fase 1 Parte D.

Modelo Camino 2 (compensatorio):

  - create (apertura): sale dinero de caja al empleado.
    Crea 1 transacción EGRESO con categoría fija Circulantes/Apertura_Circulante.
    Usuario indica proyecto + obra (para qué ámbito se abre el circulante).

  - justify (gasto): el dinero ya no está en caja pero queremos registrar
    el gasto real con la categoría/obra que corresponde.
    Crea 2 transacciones que se cancelan en neto:
      1. EGRESO con categoría real del gasto (ej. Energia/Combustible_Grupos,
         obra Monte_Chocolate_GETESA) — lo elige el usuario.
      2. INGRESO compensatorio con categoría fija Circulantes/Liquidacion_Circulante
         y mismo proyecto/obra que la transacción de egreso real.
    Resultado en caja: 0. Resultado en informes de gasto por obra: +amount.

  - close: cierre del circulante.
    Si amount_returned > 0: crea 1 transacción INGRESO con categoría fija
      Circulantes/Devolucion_Sobrante. Usuario indica proyecto + obra.
    Si amount_returned = 0: sin transacción, solo cambia estado.

Constraint conocida de BD: índice único parcial ux_floats_one_open_per_employee
impide dos circulantes abiertos para un mismo empleado.
"""
from decimal import Decimal
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import catalogs as m
from app.services.financial_helpers import get_active_session, create_transaction


# -----------------------------------------------------------------------------
# Resolución de categorías fijas
# -----------------------------------------------------------------------------
def _resolve_fixed_category(db: Session, cat_name: str, subcat_name: str):
    """Busca una categoría fija por nombre.

    Categorías usadas en circulantes (definidas en el Plan de Cuentas 2026):
      - 'Circulantes' / 'Apertura_Circulante'
      - 'Circulantes' / 'Liquidacion_Circulante'
      - 'Circulantes' / 'Devolucion_Sobrante'

    Retorna (category_id, subcategory_id). Lanza 500 si no existen.
    """
    cat = (
        db.query(m.TransactionCategory)
        .filter(m.TransactionCategory.name == cat_name)
        .first()
    )
    if not cat:
        raise HTTPException(
            status_code=500,
            detail=(
                f"Categoría '{cat_name}' no encontrada. "
                "Revise el seed del Plan de Cuentas 2026."
            ),
        )
    sub = (
        db.query(m.TransactionSubcategory)
        .filter(
            m.TransactionSubcategory.category_id == cat.id,
            m.TransactionSubcategory.name == subcat_name,
        )
        .first()
    )
    if not sub:
        raise HTTPException(
            status_code=500,
            detail=(
                f"Subcategoría '{subcat_name}' no encontrada en '{cat_name}'. "
                "Revise el seed del Plan de Cuentas 2026."
            ),
        )
    return cat.id, sub.id


# -----------------------------------------------------------------------------
# Serialización
# -----------------------------------------------------------------------------
def _to_out(db: Session, flt) -> dict:
    emp = db.query(m.Employee).filter(m.Employee.id == flt.employee_id).first()
    given    = flt.amount_given     or Decimal("0")
    justif   = flt.amount_justified or Decimal("0")
    returned = flt.amount_returned  or Decimal("0")
    return {
        "id": flt.id,
        "employee_id": flt.employee_id,
        "employee_name": emp.full_name if emp else None,
        "amount_given": given,
        "amount_justified": justif,
        "amount_returned": returned,
        "pending": given - justif - returned,
        "status": flt.status,
        "opened_at": flt.opened_at,
        "closed_at": flt.closed_at,
        "creation_transaction_id": getattr(flt, "creation_transaction_id", None),
        "close_transaction_id": getattr(flt, "close_transaction_id", None),
    }


# -----------------------------------------------------------------------------
# Operaciones públicas
# -----------------------------------------------------------------------------
def list_all(db: Session, status: str = None, employee_id: int = None):
    q = db.query(m.Float)
    if status:
        q = q.filter(m.Float.status == status)
    if employee_id:
        q = q.filter(m.Float.employee_id == employee_id)
    items = q.order_by(m.Float.opened_at.desc()).all()
    return [_to_out(db, it) for it in items]


def create(db: Session, data, user, delegacion: str):
    """Apertura del circulante.

    Valida que el empleado no tenga otro abierto. Crea la transacción de
    apertura (egreso) con categoría fija. Guarda el ID en creation_transaction_id.
    """
    # Validar que no hay otro abierto (además del constraint BD)
    existing = (
        db.query(m.Float)
        .filter(
            m.Float.employee_id == data.employee_id,
            m.Float.status.in_(["open", "partial"]),
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=409, detail="El empleado ya tiene un circulante abierto"
        )

    emp = db.query(m.Employee).filter(m.Employee.id == data.employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Empleado no encontrado")

    # Categoría fija: Circulantes / Apertura_Circulante
    cat_id, sub_id = _resolve_fixed_category(db, "Circulantes_Liquidaciones", "Apertura_Circulante")

    session = get_active_session(db, user.id, delegacion)

    concept = (
        f"[Apertura circulante] {data.concept}"
        if data.concept
        else f"[Apertura circulante] {emp.full_name}"
    )

    tx = create_transaction(
        db,
        session=session,
        user_id=user.id,
        delegacion=delegacion,
        category_id=cat_id,
        subcategory_id=sub_id,
        type_="expense",
        amount=data.amount_given,
        concept=concept,
        transaction_type="float",
        employee_id=data.employee_id,
        project_id=data.project_id,
        work_id=data.work_id,
    )

    # Insertar el circulante
    item = m.Float(
        employee_id=data.employee_id,
        amount_given=data.amount_given,
        amount_justified=Decimal("0"),
        amount_returned=Decimal("0"),
        status="open",
        opened_at=datetime.utcnow(),
        creation_transaction_id=tx.id,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return _to_out(db, item)


def justify(db: Session, float_id: int, data, user, delegacion: str):
    """Justificación de un gasto contra el circulante.

    Crea DOS transacciones:
      1. EGRESO con categoría real del gasto (la elige el usuario).
      2. INGRESO compensatorio con categoría fija Circulantes/Liquidacion_Circulante.
    Neto en caja = 0. Neto en informe de gasto real = +amount (por el egreso).
    """
    flt = db.query(m.Float).filter(m.Float.id == float_id).first()
    if not flt:
        raise HTTPException(status_code=404, detail="Circulante no encontrado")
    if flt.status == "closed":
        raise HTTPException(status_code=400, detail="Circulante cerrado")

    # Validar que no excede el importe entregado
    justified_new = (flt.amount_justified or Decimal("0")) + Decimal(data.amount)
    returned = flt.amount_returned or Decimal("0")
    if justified_new + returned > flt.amount_given:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Justificación excede: nuevo_justificado={justified_new} + "
                f"devuelto={returned} > entregado={flt.amount_given}"
            ),
        )

    emp = db.query(m.Employee).filter(m.Employee.id == flt.employee_id).first()
    session = get_active_session(db, user.id, delegacion)

    concept_base = data.concept or f"Gasto circulante {emp.full_name if emp else ''}".strip()

    # 1) Transacción EGRESO con categoría real
    tx_expense = create_transaction(
        db,
        session=session,
        user_id=user.id,
        delegacion=delegacion,
        category_id=data.category_id,
        subcategory_id=data.subcategory_id,
        type_="expense",
        amount=data.amount,
        concept=f"[Justif. circulante #{flt.id}] {concept_base}",
        transaction_type="float",
        employee_id=flt.employee_id,
        project_id=data.project_id,
        work_id=data.work_id,
    )

    # 2) Transacción INGRESO compensatorio con categoría fija
    comp_cat_id, comp_sub_id = _resolve_fixed_category(
        db, "Circulantes_Liquidaciones", "Liquidacion_Circulante"
    )
    tx_comp = create_transaction(
        db,
        session=session,
        user_id=user.id,
        delegacion=delegacion,
        category_id=comp_cat_id,
        subcategory_id=comp_sub_id,
        type_="income",
        amount=data.amount,
        concept=f"[Liquidación circulante #{flt.id}] {concept_base}",
        transaction_type="float",
        employee_id=flt.employee_id,
        project_id=data.project_id,
        work_id=data.work_id,
    )

    # Registro de justificación con ambos IDs
    jst = m.FloatJustification(
        float_id=flt.id,
        amount=data.amount,
        justified_at=datetime.utcnow(),
        expense_transaction_id=tx_expense.id,
        compensation_transaction_id=tx_comp.id,
    )
    # Compatibilidad hacia atrás: rellenar transaction_id antiguo con el egreso
    if hasattr(m.FloatJustification, "transaction_id"):
        try:
            jst.transaction_id = tx_expense.id
        except Exception:
            pass

    db.add(jst)

    flt.amount_justified = justified_new
    flt.status = "partial"
    db.commit()
    db.refresh(flt)
    return _to_out(db, flt)


def close_float(db: Session, float_id: int, data, user, delegacion: str):
    """Cierre del circulante.

    Si amount_returned > 0: crea transacción INGRESO (devolución del sobrante)
    con categoría fija Circulantes/Devolucion_Sobrante. Proyecto y obra
    obligatorios en ese caso.
    Si amount_returned = 0: solo cambia estado, sin transacción.
    """
    flt = db.query(m.Float).filter(m.Float.id == float_id).first()
    if not flt:
        raise HTTPException(status_code=404, detail="Circulante no encontrado")
    if flt.status == "closed":
        raise HTTPException(status_code=400, detail="Ya cerrado")

    amount_returned = Decimal(data.amount_returned)
    total = (flt.amount_justified or Decimal("0")) + amount_returned
    if total != flt.amount_given:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Saldo no cuadra: justificado+devuelto={total} "
                f"vs entregado={flt.amount_given}"
            ),
        )

    close_tx_id = None
    if amount_returned > 0:
        # Validar que se indique proyecto + obra
        if data.project_id is None or data.work_id is None:
            raise HTTPException(
                status_code=400,
                detail="Para registrar una devolución >0 son obligatorios proyecto y obra",
            )

        emp = db.query(m.Employee).filter(m.Employee.id == flt.employee_id).first()
        cat_id, sub_id = _resolve_fixed_category(
            db, "Circulantes_Liquidaciones", "Devolucion_Sobrante"
        )
        session = get_active_session(db, user.id, delegacion)

        concept = (
            f"[Devolución sobrante circulante #{flt.id}] "
            f"{emp.full_name if emp else ''}"
        ).strip()
        if data.notes:
            concept += f" — {data.notes}"

        tx = create_transaction(
            db,
            session=session,
            user_id=user.id,
            delegacion=delegacion,
            category_id=cat_id,
            subcategory_id=sub_id,
            type_="income",
            amount=amount_returned,
            concept=concept,
            transaction_type="float",
            employee_id=flt.employee_id,
            project_id=data.project_id,
            work_id=data.work_id,
        )
        close_tx_id = tx.id

    flt.amount_returned = amount_returned
    flt.status = "closed"
    flt.closed_at = datetime.utcnow()
    if close_tx_id is not None:
        flt.close_transaction_id = close_tx_id

    db.commit()
    db.refresh(flt)
    return _to_out(db, flt)
