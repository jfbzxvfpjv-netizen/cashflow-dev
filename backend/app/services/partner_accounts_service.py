"""Cuenta corriente de socios — M9 Fase 1 Parte E.

Cambios respecto a la versión anterior:
  - register_contribution ahora crea una transacción INGRESO en caja (bug fix).
    Categoría/subcategoría/proyecto/obra son obligatorios (schema).
  - Se unifica el retorno de todas las funciones con _movement_to_out.
  - charge_partner ya funcionaba bien, solo se limpia su retorno.
  - compensate_dividends NO crea transacción (correcto: apunte contable, no
    hay movimiento físico de efectivo).
"""
from decimal import Decimal
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import catalogs as m
from app.services.financial_helpers import get_active_session, create_transaction


def _movement_to_out(db, mv, partner=None):
    """Convierte un PartnerAccountMovement ORM a dict para PartnerMovementOut."""
    if partner is None:
        partner = db.query(m.Partner).filter(m.Partner.id == mv.partner_id).first()
    return {
        "id": mv.id,
        "partner_id": mv.partner_id,
        "partner_name": partner.full_name if partner else "?",
        "type": mv.type,
        "amount": mv.amount,
        "concept": mv.concept,
        "transaction_id": getattr(mv, "transaction_id", None),
        "created_by": getattr(mv, "created_by", None),
        "created_at": mv.created_at,
    }


def list_balances(db: Session):
    partners = db.query(m.Partner).filter(m.Partner.active == True).all()
    return [
        {
            "partner_id": p.id,
            "partner_name": p.full_name,
            "participation_pct": p.participation_pct or Decimal("0"),
            "current_balance": p.current_balance or Decimal("0"),
        }
        for p in partners
    ]


def list_movements(db: Session, partner_id: int = None):
    q = db.query(m.PartnerAccountMovement)
    if partner_id:
        q = q.filter(m.PartnerAccountMovement.partner_id == partner_id)
    items = q.order_by(m.PartnerAccountMovement.id.desc()).all()
    out = []
    for it in items:
        p = db.query(m.Partner).filter(m.Partner.id == it.partner_id).first()
        out.append(_movement_to_out(db, it, partner=p))
    return out


def charge_partner(db: Session, data, user, delegacion: str):
    """Cargo a cuenta de socio: la organización paga por él, aumenta su deuda.

    Crea transacción EGRESO (la empresa saca dinero de caja para pagar
    algo por cuenta del socio). El saldo del socio sube (deuda).
    """
    partner = db.query(m.Partner).filter(m.Partner.id == data.partner_id).first()
    if not partner:
        raise HTTPException(status_code=404, detail="Socio no encontrado")

    session = get_active_session(db, user.id, delegacion)
    tx = create_transaction(
        db,
        session=session,
        user_id=user.id,
        delegacion=delegacion,
        category_id=data.category_id,
        subcategory_id=data.subcategory_id,
        type_="expense",
        amount=data.amount,
        concept=f"[Cargo socio {partner.full_name}] {data.concept}",
        transaction_type="partner_charge",
        partner_id=data.partner_id,
        project_id=data.project_id,
        work_id=data.work_id,
    )

    partner.current_balance = (partner.current_balance or Decimal("0")) + Decimal(data.amount)
    mv = m.PartnerAccountMovement(
        partner_id=partner.id,
        type="charge",
        amount=data.amount,
        concept=data.concept,
        transaction_id=tx.id,
        created_by=user.id,
        created_at=datetime.utcnow(),
    )
    db.add(mv)
    db.commit()
    db.refresh(mv)
    return _movement_to_out(db, mv, partner=partner)


def register_contribution(db: Session, data, user, delegacion: str):
    """Aportación del socio: socio mete dinero físico a caja.

    BUG FIX de Parte E: antes no creaba transacción en caja.
    Ahora crea transacción INGRESO. Saldo de caja sube. Saldo del socio
    baja (deja de deberle la empresa).
    """
    partner = db.query(m.Partner).filter(m.Partner.id == data.partner_id).first()
    if not partner:
        raise HTTPException(status_code=404, detail="Socio no encontrado")
    if not partner.can_contribute:
        raise HTTPException(
            status_code=403, detail="Este socio no puede realizar aportaciones"
        )

    session = get_active_session(db, user.id, delegacion)
    tx = create_transaction(
        db,
        session=session,
        user_id=user.id,
        delegacion=delegacion,
        category_id=data.category_id,
        subcategory_id=data.subcategory_id,
        type_="income",
        amount=data.amount,
        concept=f"[Aportación socio {partner.full_name}] {data.concept}",
        transaction_type="partner_contribution",
        partner_id=data.partner_id,
        project_id=data.project_id,
        work_id=data.work_id,
    )

    partner.current_balance = (partner.current_balance or Decimal("0")) - Decimal(data.amount)
    mv = m.PartnerAccountMovement(
        partner_id=partner.id,
        type="contribution",
        amount=data.amount,
        concept=data.concept,
        transaction_id=tx.id,
        created_by=user.id,
        created_at=datetime.utcnow(),
    )
    db.add(mv)
    db.commit()
    db.refresh(mv)
    return _movement_to_out(db, mv, partner=partner)


def compensate_dividends(db: Session, data, user, delegacion: str):
    """Compensación de dividendos: reduce saldo deudor del socio.

    NO crea transacción en caja — es un apunte contable interno entre la
    empresa y el socio (se aplican dividendos contra deuda existente).
    No hay movimiento físico de efectivo.
    """
    partner = db.query(m.Partner).filter(m.Partner.id == data.partner_id).first()
    if not partner:
        raise HTTPException(status_code=404, detail="Socio no encontrado")

    partner.current_balance = (partner.current_balance or Decimal("0")) - Decimal(data.amount)
    mv = m.PartnerAccountMovement(
        partner_id=partner.id,
        type="dividend_compensation",
        amount=data.amount,
        concept=data.concept,
        created_by=user.id,
        created_at=datetime.utcnow(),
    )
    db.add(mv)
    db.commit()
    db.refresh(mv)
    return _movement_to_out(db, mv, partner=partner)
