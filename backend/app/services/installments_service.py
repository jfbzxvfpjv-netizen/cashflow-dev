"""Pagos fraccionados — total conocido desde el inicio."""
from decimal import Decimal
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models import catalogs as m
from app.services.financial_helpers import get_active_session, create_transaction


def _to_out(db, ip):
    """Serializa un InstallmentPayment con campos calculados."""
    from decimal import Decimal
    supp = db.query(m.Supplier).filter(m.Supplier.id == ip.supplier_id).first() if ip.supplier_id else None
    emp  = db.query(m.Employee).filter(m.Employee.id == ip.employee_id).first() if ip.employee_id else None
    installments_paid = db.query(m.InstallmentRecord).filter(m.InstallmentRecord.installment_payment_id == ip.id).count()
    total = ip.total_amount or Decimal("0")
    paid  = ip.amount_paid  or Decimal("0")
    return {
        "id": ip.id,
        "total_amount": total,
        "concept": ip.concept,
        "supplier_id": ip.supplier_id,
        "supplier_name": supp.name if supp else None,
        "employee_id": ip.employee_id,
        "employee_name": emp.full_name if emp else None,
        "amount_paid": paid,
        "pending": total - paid,
        "installments_count": ip.installments_count,
        "installments_paid": installments_paid,
        "status": ip.status,
        "default_category_id": ip.default_category_id,
        "default_subcategory_id": ip.default_subcategory_id,
        "default_project_id": ip.default_project_id,
        "default_work_id": ip.default_work_id,
        "created_at": ip.created_at,
    }



def list_all(db: Session, status: str = None):
    q = db.query(m.InstallmentPayment)
    if status:
        q = q.filter(m.InstallmentPayment.status == status)
    items = q.order_by(m.InstallmentPayment.id.desc()).all()
    out = []
    for it in items:
        sup = db.query(m.Supplier).filter(m.Supplier.id == it.supplier_id).first() if it.supplier_id else None
        emp = db.query(m.Employee).filter(m.Employee.id == it.employee_id).first() if it.employee_id else None
        paid_count = db.query(m.InstallmentRecord).filter(m.InstallmentRecord.installment_payment_id == it.id).count()
        out.append({
            "id": it.id, "total_amount": it.total_amount, "concept": it.concept,
            "amount_paid": it.amount_paid or Decimal("0"),
            "pending": (it.total_amount or Decimal("0")) - (it.amount_paid or Decimal("0")),
            "installments_count": it.installments_count,
            "installments_paid": paid_count, "status": it.status,
            "supplier_id": it.supplier_id, "employee_id": it.employee_id,
            "supplier_name": sup.name if sup else None,
            "employee_name": emp.full_name if emp else None,
        })
    return out


def create(db: Session, data, user_id: int):
    if not data.supplier_id and not data.employee_id:
        raise HTTPException(status_code=400, detail="Indique proveedor o empleado")
    item = m.InstallmentPayment(
        total_amount=data.total_amount, concept=data.concept,
        installments_count=data.installments_count,
        supplier_id=data.supplier_id, employee_id=data.employee_id,
        amount_paid=Decimal("0"), status="active",
        default_category_id=data.default_category_id,
        default_subcategory_id=data.default_subcategory_id,
        default_project_id=data.default_project_id,
        default_work_id=data.default_work_id,
    )
    db.add(item); db.commit(); db.refresh(item)
    return _to_out(db, item)


def pay_installment(db: Session, installment_id: int, data, user, delegacion: str):
    item = db.query(m.InstallmentPayment).filter(m.InstallmentPayment.id == installment_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Pago fraccionado no encontrado")
    if item.status == "closed":
        raise HTTPException(status_code=400, detail="Pago fraccionado ya cerrado")
    paid = (item.amount_paid or Decimal("0")) + Decimal(data.amount)
    if paid > item.total_amount:
        raise HTTPException(status_code=400, detail="El pago excede el total pendiente")
    session = get_active_session(db, user.id, delegacion)
    tx = create_transaction(
        db, session=session, user_id=user.id, delegacion=delegacion,
        category_id=data.category_id, subcategory_id=data.subcategory_id,
        type_="expense", amount=data.amount,
        concept=f"[Plazo] {item.concept}",
        transaction_type="installment",
        supplier_id=item.supplier_id, employee_id=item.employee_id,
        project_id=data.project_id, work_id=data.work_id,
    )
    rec = m.InstallmentRecord(
        installment_payment_id=item.id, transaction_id=tx.id,
        amount=data.amount, paid_at=datetime.utcnow(),
    )
    db.add(rec)
    item.amount_paid = paid
    if paid == item.total_amount:
        item.status = "closed"
    db.commit(); db.refresh(item)
    return _to_out(db, item)