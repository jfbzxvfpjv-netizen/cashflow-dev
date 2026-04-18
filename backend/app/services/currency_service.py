"""Servicio M9 — Operaciones en divisa (compra y entrega de EUR).

Reglas:
  - Comprar euros: sale dinero en XAF de la caja → transacción expense
    real. Incrementa stock EUR de la delegación.
  - Entregar euros: NO afecta caja XAF (el dinero ya salió al comprar).
    Solo decrementa stock EUR. Registro documental en currency_operations.
"""
from decimal import Decimal
from datetime import datetime, timedelta
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import catalogs as m
from app.services.financial_helpers import get_active_session, create_transaction


def get_stock(db: Session, delegacion: str):
    stk = db.query(m.EurStock).filter(m.EurStock.delegacion == delegacion).first()
    if not stk:
        stk = m.EurStock(delegacion=delegacion, current_eur_stock=Decimal("0"))
        db.add(stk); db.commit(); db.refresh(stk)
    return stk


def list_operations(db: Session, delegacion: str = None):
    q = db.query(m.CurrencyOperation)
    if delegacion:
        q = q.filter(m.CurrencyOperation.delegacion == delegacion)
    items = q.order_by(m.CurrencyOperation.id.desc()).all()
    return [_to_out(db, op) for op in items]


def _to_out(db, op):
    return {
        "id": op.id,
        "delegacion": op.delegacion,
        "op_type": op.op_type,
        "xaf_amount": op.xaf_amount,
        "eur_amount": op.eur_amount,
        "exchange_rate": op.exchange_rate,
        "exchange_office": op.exchange_office,
        "eur_stock_after": op.eur_stock_after,
        "buy_transaction_id": op.buy_transaction_id,
        "delivery_transaction_id": op.delivery_transaction_id,
        "created_at": op.created_at,
        "editable_until": op.editable_until,
        "cancelled": op.cancelled or False,
        "cancelled_at": op.cancelled_at,
        "cancel_reason": op.cancel_reason,
    }


def buy_euros(db: Session, data, user, delegacion: str):
    """Compra de euros: egreso de XAF en caja + incremento de stock EUR."""
    session = get_active_session(db, user.id, delegacion)
    stk = get_stock(db, delegacion)
    rate = Decimal(data.xaf_amount) / Decimal(data.eur_amount)

    buy_tx = create_transaction(
        db, session=session, user_id=user.id, delegacion=delegacion,
        category_id=data.category_id, subcategory_id=data.subcategory_id,
        type_="expense", amount=data.xaf_amount,
        concept=f"Compra de {data.eur_amount}€ — {data.exchange_office} (tasa {rate:.2f})",
        transaction_type="currency_exchange",
        counterparty_free=data.exchange_office,
        project_id=data.project_id, work_id=data.work_id,
    )

    stk.current_eur_stock = (stk.current_eur_stock or Decimal("0")) + Decimal(data.eur_amount)
    stk.last_updated = datetime.utcnow()

    op = m.CurrencyOperation(
        delegacion=delegacion,
        op_type="buy",
        xaf_amount=data.xaf_amount, eur_amount=data.eur_amount,
        exchange_rate=rate, exchange_office=data.exchange_office,
        buy_transaction_id=buy_tx.id, eur_stock_after=stk.current_eur_stock,
        created_at=datetime.utcnow(),
        editable_until=datetime.utcnow() + timedelta(minutes=15),
    )
    db.add(op); db.commit(); db.refresh(op)
    return _to_out(db, op)


def deliver_euros(db: Session, data, user, delegacion: str):
    """Entrega de euros a destinatario. NO afecta la caja XAF — el dinero ya
    salió al comprar. Solo decrementa stock EUR y deja registro documental."""
    # Validación de sesión abierta (por consistencia con patrón M9)
    get_active_session(db, user.id, delegacion)

    stk = get_stock(db, delegacion)
    if stk.current_eur_stock < Decimal(data.eur_amount):
        raise HTTPException(
            status_code=400,
            detail=f"Stock EUR insuficiente en {delegacion}: {stk.current_eur_stock}€"
        )

    rate = Decimal(data.xaf_equivalent) / Decimal(data.eur_amount)

    stk.current_eur_stock = stk.current_eur_stock - Decimal(data.eur_amount)
    stk.last_updated = datetime.utcnow()

    op = m.CurrencyOperation(
        delegacion=delegacion,
        op_type="deliver",
        xaf_amount=data.xaf_equivalent, eur_amount=data.eur_amount,
        exchange_rate=rate, exchange_office=data.recipient,
        eur_stock_after=stk.current_eur_stock,
        created_at=datetime.utcnow(),
        editable_until=datetime.utcnow() + timedelta(minutes=15),
    )
    db.add(op); db.commit(); db.refresh(op)
    return _to_out(db, op)


def edit_delivery(db: Session, op_id: int, data, user):
    """Edita una entrega de euros dentro de la ventana de 15 min (o 30 días para admin)."""
    op = db.query(m.CurrencyOperation).filter(m.CurrencyOperation.id == op_id).first()
    if not op:
        raise HTTPException(status_code=404, detail="Operación no encontrada")
    if op.op_type != "deliver":
        raise HTTPException(status_code=400, detail="Solo se pueden editar entregas (deliver)")
    if op.cancelled:
        raise HTTPException(status_code=400, detail="La operación está cancelada, no se puede editar")

    now = datetime.utcnow()
    is_admin = getattr(user, "role", "") == "admin"
    admin_window_ok = is_admin and (now - op.created_at) < timedelta(days=30)
    native_window_ok = op.editable_until and now <= op.editable_until

    if not native_window_ok and not admin_window_ok:
        raise HTTPException(status_code=403, detail="Ventana de edición expirada")
    if admin_window_ok and not native_window_ok and not (data.reason and len(data.reason.strip()) >= 3):
        raise HTTPException(status_code=400, detail="Admin debe indicar motivo para editar fuera de ventana")

    # Ajuste de stock si cambian los euros
    stk = get_stock(db, op.delegacion)
    old_eur = Decimal(op.eur_amount or 0)
    new_eur = Decimal(data.eur_amount) if data.eur_amount is not None else old_eur

    if new_eur != old_eur:
        # Deshacer el descuento anterior y aplicar el nuevo
        # (original: stock -= old_eur → ahora: stock += old_eur - new_eur)
        delta = old_eur - new_eur  # positivo si el nuevo es menor → devuelve stock
        candidate_stock = (stk.current_eur_stock or Decimal("0")) + delta
        if candidate_stock < Decimal("0"):
            raise HTTPException(status_code=400, detail=f"El nuevo importe ({new_eur}€) dejaría el stock negativo")
        stk.current_eur_stock = candidate_stock
        stk.last_updated = now

    # Aplicar cambios
    if data.eur_amount is not None:
        op.eur_amount = new_eur
    if data.xaf_equivalent is not None:
        op.xaf_amount = data.xaf_equivalent
        if new_eur > 0:
            op.exchange_rate = Decimal(data.xaf_equivalent) / new_eur
    if data.recipient is not None:
        op.exchange_office = data.recipient  # en deliver, exchange_office guarda el recipient
    op.eur_stock_after = stk.current_eur_stock

    db.commit(); db.refresh(op)
    return _to_out(db, op)


def cancel_operation(db: Session, op_id: int, data, user):
    """Anula una operación de divisa. Por ahora solo entregas — las compras
    requieren cancelar la transacción XAF asociada con contrapartida (TODO)."""
    op = db.query(m.CurrencyOperation).filter(m.CurrencyOperation.id == op_id).first()
    if not op:
        raise HTTPException(status_code=404, detail="Operación no encontrada")
    if op.cancelled:
        raise HTTPException(status_code=400, detail="Ya está cancelada")
    if op.op_type != "deliver":
        raise HTTPException(status_code=400, detail="Por ahora solo se pueden anular entregas (deliver)")

    stk = get_stock(db, op.delegacion)
    # Al cancelar una entrega: los euros vuelven al stock
    stk.current_eur_stock = (stk.current_eur_stock or Decimal("0")) + Decimal(op.eur_amount)
    stk.last_updated = datetime.utcnow()

    op.cancelled = True
    op.cancelled_at = datetime.utcnow()
    op.cancelled_by_user_id = user.id
    op.cancel_reason = data.reason

    db.commit(); db.refresh(op)
    return _to_out(db, op)