"""Envíos de dinero — Western Union, MoneyGram, operadores locales."""
from decimal import Decimal
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models import catalogs as m
from app.services.financial_helpers import get_active_session, create_transaction


OPERATOR_LABELS = {
    "western_union": "Western Union",
    "moneygram": "MoneyGram",
    "operador_local": "Operador local",
}

DIRECTION_LABELS = {
    "sent": "Enviado",
    "received": "Recibido",
}


def _row_to_dict(it, commission_amount):
    """Serializa un MoneyTransfer + comisión resuelta a dict para el schema Out."""
    return {
        "id": it.id,
        "operator": it.operator,
        "reference_number": it.reference_number,
        "sender_name": it.sender_name,
        "receiver_name": it.receiver_name,
        "sender_id": it.sender_id,
        "receiver_id": it.receiver_id,
        "amount": it.amount,
        "direction": it.direction,
        "delegacion_origin": it.delegacion_origin,
        "delegacion_dest": it.delegacion_dest,
        "commission_transaction_id": it.commission_transaction_id,
        "commission_amount": commission_amount,
        "operator_label": OPERATOR_LABELS.get(it.operator, it.operator),
        "direction_label": DIRECTION_LABELS.get(it.direction, it.direction),
        "created_at": it.created_at,
    }


def _base_query(db: Session):
    """Query base: MoneyTransfer LEFT JOIN Transaction para resolver amount de comisión."""
    return (db.query(
                m.MoneyTransfer,
                m.Transaction.amount.label("commission_amount"),
            )
            .outerjoin(m.Transaction, m.Transaction.id == m.MoneyTransfer.commission_transaction_id))


def list_all(db: Session, operator: str = None, direction: str = None):
    q = _base_query(db)
    if operator:
        q = q.filter(m.MoneyTransfer.operator == operator)
    if direction:
        q = q.filter(m.MoneyTransfer.direction == direction)
    rows = q.order_by(m.MoneyTransfer.id.desc()).all()
    return [_row_to_dict(it, cm) for it, cm in rows]


def _fetch_one(db: Session, transfer_id: int):
    row = _base_query(db).filter(m.MoneyTransfer.id == transfer_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Envío no encontrado tras operación")
    it, cm = row
    return _row_to_dict(it, cm)


def create(db: Session, data, user, delegacion: str):
    """Crea un envío de dinero. Genera la transacción principal en caja y,
    si hay comisión, una transacción adicional. Autoasigna las delegaciones
    origen/destino según direction si no vienen en el payload."""
    session = get_active_session(db, user.id, delegacion)

    # Autoasignación de delegación según dirección si no viene del cliente.
    # Si direction='sent': origen = delegación deducida; dest = lo que venga (puede ser null = exterior).
    # Si direction='received': dest = delegación deducida; origen = lo que venga (puede ser null = exterior).
    if data.direction == "sent":
        deleg_origin = data.delegacion_origin or delegacion
        deleg_dest = data.delegacion_dest
        tx_type = "expense"
    else:
        deleg_dest = data.delegacion_dest or delegacion
        deleg_origin = data.delegacion_origin
        tx_type = "income"

    tx = create_transaction(
        db, session=session, user_id=user.id, delegacion=delegacion,
        category_id=data.category_id, subcategory_id=data.subcategory_id,
        type_=tx_type, amount=data.amount,
        concept=f"[{data.operator}] {data.sender_name} → {data.receiver_name} ({data.reference_number})",
        transaction_type="money_transfer",
        counterparty_free=f"{data.sender_name} / {data.receiver_name}",
        project_id=data.project_id, work_id=data.work_id,
    )

    commission_tx_id = None
    if Decimal(data.commission) > 0:
        ctx = create_transaction(
            db, session=session, user_id=user.id, delegacion=delegacion,
            category_id=data.category_id, subcategory_id=data.subcategory_id,
            type_="expense", amount=data.commission,
            concept=f"Comisión {data.operator} {data.reference_number}",
            transaction_type="money_transfer",
            counterparty_free=data.operator,
            project_id=data.project_id, work_id=data.work_id,
        )
        commission_tx_id = ctx.id

    item = m.MoneyTransfer(
        operator=data.operator,
        reference_number=data.reference_number,
        sender_name=data.sender_name,
        receiver_name=data.receiver_name,
        sender_id=data.sender_id,
        receiver_id=data.receiver_id,
        amount=data.amount,
        commission_transaction_id=commission_tx_id,
        direction=data.direction,
        delegacion_origin=deleg_origin,
        delegacion_dest=deleg_dest,
        created_at=datetime.utcnow(),
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return _fetch_one(db, item.id)


def inter_delegation_position(db: Session):
    """Posición neta de transferencias Bata ↔ Malabo."""
    bata_to_malabo = db.query(m.MoneyTransfer).filter(
        m.MoneyTransfer.delegacion_origin == "Bata",
        m.MoneyTransfer.delegacion_dest == "Malabo",
    ).all()
    malabo_to_bata = db.query(m.MoneyTransfer).filter(
        m.MoneyTransfer.delegacion_origin == "Malabo",
        m.MoneyTransfer.delegacion_dest == "Bata",
    ).all()
    btm = sum((Decimal(x.amount) for x in bata_to_malabo), Decimal("0"))
    mtb = sum((Decimal(x.amount) for x in malabo_to_bata), Decimal("0"))
    net = btm - mtb
    favor = None
    if net > 0:
        favor = "Malabo (recibe más de Bata)"
    elif net < 0:
        favor = "Bata (recibe más de Malabo)"
    return {
        "bata_to_malabo": btm,
        "malabo_to_bata": mtb,
        "net_position": abs(net),
        "favor_delegation": favor,
    }