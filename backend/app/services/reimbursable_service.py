"""Gastos reembolsables — Fix Reimbursable.

Cambios respecto a la versión anterior:

1. Validación: al menos uno de partner_id o employee_id debe venir poblado.
   Si vienen los dos, se rechaza (el reembolsable es de UN destinatario).

2. El usuario elige subcategoría al CREAR (no al reembolsar).
   Elimina la heurística SUBCAT_BY_METHOD fallida.

3. La transacción de reembolso (egreso en caja) rellena:
   - partner_id o employee_id según corresponda (contraparte visible en tabla).
   - subcategory_id elegida al crear el reembolsable.
   - concept incluye el nombre del destinatario.

4. list_all y _fetch_with_names resuelven partner_name y employee_name.
"""
from decimal import Decimal
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import catalogs as m
from app.services.financial_helpers import get_active_session, create_transaction


def _row_to_dict(it, cat_name, proj_name, work_name, subcat_name=None,
                 partner_name=None, employee_name=None):
    """Serializa un ReimbursableExpense a dict con nombres resueltos."""
    pending = (it.amount_xaf or Decimal("0")) - (it.amount_reimbursed or Decimal("0"))
    return {
        "id": it.id,
        "amount_eur": it.amount_eur,
        "amount_xaf": it.amount_xaf,
        "exchange_rate": it.exchange_rate,
        "payment_method": it.payment_method,
        "concept": it.concept,
        "status": it.status,
        "amount_reimbursed": it.amount_reimbursed or Decimal("0"),
        "pending_xaf": pending,
        "created_at": it.created_at,
        "category_id": it.category_id,
        "subcategory_id": getattr(it, "subcategory_id", None),
        "project_id": it.project_id,
        "work_id": it.work_id,
        "partner_id": getattr(it, "partner_id", None),
        "employee_id": getattr(it, "employee_id", None),
        "category_name": cat_name,
        "subcategory_name": subcat_name,
        "project_name": proj_name,
        "work_name": work_name,
        "partner_name": partner_name,
        "employee_name": employee_name,
    }


def _resolve_counterparty_name(db: Session, it: m.ReimbursableExpense):
    """Devuelve (partner_name, employee_name) según qué FK tenga poblada."""
    partner_name = None
    employee_name = None
    if getattr(it, "partner_id", None):
        p = db.query(m.Partner).filter(m.Partner.id == it.partner_id).first()
        partner_name = p.full_name if p else None
    if getattr(it, "employee_id", None):
        e = db.query(m.Employee).filter(m.Employee.id == it.employee_id).first()
        employee_name = e.full_name if e else None
    return partner_name, employee_name


def list_all(db: Session, status: str = None):
    q = (db.query(
            m.ReimbursableExpense,
            m.TransactionCategory.name.label("cat_name"),
            m.Project.name.label("proj_name"),
            m.Work.name.label("work_name"),
            m.TransactionSubcategory.name.label("sub_name"),
        )
        .outerjoin(m.TransactionCategory, m.TransactionCategory.id == m.ReimbursableExpense.category_id)
        .outerjoin(m.Project, m.Project.id == m.ReimbursableExpense.project_id)
        .outerjoin(m.Work, m.Work.id == m.ReimbursableExpense.work_id)
        .outerjoin(m.TransactionSubcategory, m.TransactionSubcategory.id == m.ReimbursableExpense.subcategory_id)
    )
    if status:
        q = q.filter(m.ReimbursableExpense.status == status)
    rows = q.order_by(m.ReimbursableExpense.id.desc()).all()
    out = []
    for it, c, p, w, sub in rows:
        pname, ename = _resolve_counterparty_name(db, it)
        out.append(_row_to_dict(it, c, p, w, sub, pname, ename))
    return out


def _fetch_with_names(db: Session, item_id: int):
    row = (db.query(
            m.ReimbursableExpense,
            m.TransactionCategory.name.label("cat_name"),
            m.Project.name.label("proj_name"),
            m.Work.name.label("work_name"),
            m.TransactionSubcategory.name.label("sub_name"),
        )
        .outerjoin(m.TransactionCategory, m.TransactionCategory.id == m.ReimbursableExpense.category_id)
        .outerjoin(m.Project, m.Project.id == m.ReimbursableExpense.project_id)
        .outerjoin(m.Work, m.Work.id == m.ReimbursableExpense.work_id)
        .outerjoin(m.TransactionSubcategory, m.TransactionSubcategory.id == m.ReimbursableExpense.subcategory_id)
        .filter(m.ReimbursableExpense.id == item_id)
        .first())
    if not row:
        raise HTTPException(status_code=404, detail="Gasto reembolsable no encontrado tras operación")
    it, c, p, w, sub = row
    pname, ename = _resolve_counterparty_name(db, it)
    return _row_to_dict(it, c, p, w, sub, pname, ename)


def create(db: Session, data, user_id: int):
    """Crea un gasto reembolsable.

    Validaciones:
      - Debe venir al menos uno de partner_id o employee_id.
      - No pueden venir los dos a la vez (destinatario único).
      - subcategory_id obligatorio y debe pertenecer a category_id.
    """
    partner_id = getattr(data, "partner_id", None)
    employee_id = getattr(data, "employee_id", None)

    if not partner_id and not employee_id:
        raise HTTPException(
            status_code=400,
            detail="Debe indicar socio o empleado (quién adelantó el dinero)",
        )
    if partner_id and employee_id:
        raise HTTPException(
            status_code=400,
            detail="Indique solo uno: socio o empleado, no ambos",
        )

    subcategory_id = getattr(data, "subcategory_id", None)
    if not subcategory_id:
        raise HTTPException(
            status_code=400,
            detail="La subcategoría es obligatoria",
        )

    # Validar que la subcategoría pertenece a la categoría
    sub = (db.query(m.TransactionSubcategory)
           .filter(m.TransactionSubcategory.id == subcategory_id,
                   m.TransactionSubcategory.category_id == data.category_id)
           .first())
    if not sub:
        raise HTTPException(
            status_code=400,
            detail="La subcategoría no pertenece a la categoría indicada",
        )

    # Validar contraparte existe
    if partner_id:
        p = db.query(m.Partner).filter(m.Partner.id == partner_id).first()
        if not p:
            raise HTTPException(status_code=404, detail="Socio no encontrado")
    if employee_id:
        e = db.query(m.Employee).filter(m.Employee.id == employee_id).first()
        if not e:
            raise HTTPException(status_code=404, detail="Empleado no encontrado")

    eur = Decimal(data.amount_eur)
    xaf = Decimal(data.amount_xaf)
    rate = (xaf / eur) if eur > 0 else Decimal("0")

    item = m.ReimbursableExpense(
        amount_eur=eur,
        amount_xaf=xaf,
        exchange_rate=rate,
        payment_method=data.payment_method,
        concept=data.concept,
        category_id=data.category_id,
        subcategory_id=subcategory_id,
        project_id=data.project_id,
        work_id=data.work_id,
        partner_id=partner_id,
        employee_id=employee_id,
        status="pending",
        amount_reimbursed=Decimal("0"),
        created_by=user_id,
        created_at=datetime.utcnow(),
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return _fetch_with_names(db, item.id)


def reimburse(db: Session, item_id: int, data, user, delegacion: str):
    """Registra un reembolso parcial o total como transacción egreso.

    La transacción lleva:
      - partner_id o employee_id según el reembolsable (para trazabilidad).
      - subcategory_id elegida al crear el reembolsable.
      - concept con el nombre del destinatario incluido.
    """
    item = db.query(m.ReimbursableExpense).filter(m.ReimbursableExpense.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Gasto reembolsable no encontrado")
    if item.status == "reimbursed":
        raise HTTPException(status_code=400, detail="Ya reembolsado totalmente")

    pending = item.amount_xaf - (item.amount_reimbursed or Decimal("0"))
    amount = Decimal(data.amount_xaf)
    if amount > pending:
        raise HTTPException(status_code=400, detail="El importe excede el pendiente de reembolsar")
    if amount <= 0:
        raise HTTPException(status_code=400, detail="El importe debe ser mayor que cero")

    # Determinar destinatario y su nombre
    partner_id = getattr(item, "partner_id", None)
    employee_id = getattr(item, "employee_id", None)
    target_name = "?"
    if partner_id:
        p = db.query(m.Partner).filter(m.Partner.id == partner_id).first()
        target_name = p.full_name if p else "socio"
    elif employee_id:
        e = db.query(m.Employee).filter(m.Employee.id == employee_id).first()
        target_name = e.full_name if e else "empleado"

    # Subcategoría: usar la que eligió al crear
    subcategory_id = getattr(item, "subcategory_id", None)
    if not subcategory_id:
        # Fallback para registros antiguos: usar la primera subcategoría de la
        # categoría (compatibilidad con datos previos al fix).
        sub = (db.query(m.TransactionSubcategory)
               .filter(m.TransactionSubcategory.category_id == item.category_id)
               .first())
        if not sub:
            raise HTTPException(
                status_code=400,
                detail="No hay subcategoría disponible para el reembolso",
            )
        subcategory_id = sub.id

    session = get_active_session(db, user.id, delegacion)

    create_transaction(
        db,
        session=session,
        user_id=user.id,
        delegacion=delegacion,
        category_id=item.category_id,
        subcategory_id=subcategory_id,
        type_="expense",
        amount=amount,
        concept=f"[Reembolso a {target_name}] {item.concept}",
        transaction_type="reimbursable",
        partner_id=partner_id,
        employee_id=employee_id,
        project_id=item.project_id,
        work_id=item.work_id,
    )

    item.amount_reimbursed = (item.amount_reimbursed or Decimal("0")) + amount
    item.status = "reimbursed" if item.amount_reimbursed >= item.amount_xaf else "partial"
    db.commit()
    db.refresh(item)
    return _fetch_with_names(db, item.id)
