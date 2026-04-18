"""Modelos SQLAlchemy — M9 Módulos Financieros Especiales (Capa 2).

Este fichero contiene las 11 clases ORM que mapean las tablas creadas por
el DDL de M9. Se re-exporta desde catalogs.py para mantener el patrón
`from app.models import catalogs as m; m.AdvanceLoan`.
"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Numeric, Text, DateTime, Date, Boolean,
    ForeignKey, CheckConstraint
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship
from app.models.catalogs import Base  # reutiliza Base de M1


class AdvanceLoan(Base):
    __tablename__ = "advances_loans"
    __table_args__ = {"extend_existing": True}
    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    type = Column(String(10), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    concept = Column(Text, nullable=False)
    status = Column(String(10), nullable=False, default="open")
    amount_repaid = Column(Numeric(12, 2), nullable=False, default=0)
    opened_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    closed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    # M9 Fase 1 — vinculación con transacciones en caja
    creation_transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=True)
    repay_transaction_ids = Column(ARRAY(Integer), nullable=False, default=list)


class RetentionDeposit(Base):
    __tablename__ = "retentions_deposits"
    __table_args__ = {"extend_existing": True}
    id = Column(Integer, primary_key=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    type = Column(String(15), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    concept = Column(Text, nullable=False)
    status = Column(String(10), nullable=False, default="pending")
    release_date = Column(Date, nullable=True)
    released_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    # M9 Fase 1 Parte C — vinculación con transacciones en caja
    creation_transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=True)
    release_transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=True)


class Float(Base):
    __tablename__ = "floats"
    __table_args__ = {"extend_existing": True}
    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    amount_given = Column(Numeric(12, 2), nullable=False)
    amount_justified = Column(Numeric(12, 2), nullable=False, default=0)
    amount_returned = Column(Numeric(12, 2), nullable=False, default=0)
    status = Column(String(10), nullable=False, default="open")
    opened_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    closed_at = Column(DateTime, nullable=True)
    # M9 Fase 1 Parte D — vinculación con transacciones de caja
    creation_transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=True)
    close_transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class FloatJustification(Base):
    __tablename__ = "float_justifications"
    __table_args__ = {"extend_existing": True}
    id = Column(Integer, primary_key=True)
    float_id = Column(Integer, ForeignKey("floats.id", ondelete="CASCADE"), nullable=False)
    transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    justified_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    # M9 Fase 1 Parte D (hotfix) — dos transacciones compensatorias
    expense_transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=True)
    compensation_transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=True)


class InstallmentPayment(Base):
    __tablename__ = "installment_payments"
    __table_args__ = {"extend_existing": True}
    id = Column(Integer, primary_key=True)
    total_amount = Column(Numeric(12, 2), nullable=False)
    concept = Column(Text, nullable=False)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    amount_paid = Column(Numeric(12, 2), nullable=False, default=0)
    installments_count = Column(Integer, nullable=False, default=0)
    status = Column(String(10), nullable=False, default="active")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    default_category_id    = Column(Integer, ForeignKey("transaction_categories.id"), nullable=True)
    default_subcategory_id = Column(Integer, ForeignKey("transaction_subcategories.id"), nullable=True)
    default_project_id     = Column(Integer, ForeignKey("projects.id"), nullable=True)
    default_work_id        = Column(Integer, ForeignKey("works.id"), nullable=True)


class InstallmentRecord(Base):
    __tablename__ = "installment_records"
    __table_args__ = {"extend_existing": True}
    id = Column(Integer, primary_key=True)
    installment_payment_id = Column(Integer, ForeignKey("installment_payments.id", ondelete="CASCADE"), nullable=False)
    transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    paid_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class CurrencyOperation(Base):
    __tablename__ = "currency_operations"
    __table_args__ = {"extend_existing": True}
    id = Column(Integer, primary_key=True)
    xaf_amount = Column(Numeric(14, 2), nullable=False)
    eur_amount = Column(Numeric(12, 2), nullable=False)
    exchange_rate = Column(Numeric(10, 4), nullable=False)
    exchange_office = Column(String(100), nullable=True)
    buy_transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=True)
    delivery_transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=True)
    eur_stock_after = Column(Numeric(12, 2), nullable=True)
    delegacion = Column(String(10), nullable=False)
    op_type = Column(String(10), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    editable_until       = Column(DateTime, nullable=True)
    cancelled            = Column(Boolean, nullable=False, default=False)
    cancelled_at         = Column(DateTime, nullable=True)
    cancelled_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    cancel_reason        = Column(Text, nullable=True)


class EurStock(Base):
    __tablename__ = "eur_stock"
    __table_args__ = {"extend_existing": True}
    id = Column(Integer, primary_key=True)
    delegacion = Column(String(10), unique=True, nullable=False)
    current_eur_stock = Column(Numeric(12, 2), nullable=False, default=0)
    last_updated = Column(DateTime, nullable=False, default=datetime.utcnow)


class PartnerAccountMovement(Base):
    __tablename__ = "partner_account_movements"
    __table_args__ = {"extend_existing": True}
    id = Column(Integer, primary_key=True)
    partner_id = Column(Integer, ForeignKey("partners.id"), nullable=False)
    type = Column(String(25), nullable=False)
    amount = Column(Numeric(14, 2), nullable=False)
    concept = Column(Text, nullable=False)
    transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class ReimbursableExpense(Base):
    __tablename__ = "reimbursable_expenses"
    __table_args__ = {"extend_existing": True}
    id = Column(Integer, primary_key=True)
    amount_eur = Column(Numeric(12, 2), nullable=False)
    amount_xaf = Column(Numeric(14, 2), nullable=False)
    exchange_rate = Column(Numeric(10, 4), nullable=False)
    payment_method = Column(String(30), nullable=False)
    concept = Column(Text, nullable=False)
    category_id = Column(Integer, ForeignKey("transaction_categories.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    work_id = Column(Integer, ForeignKey("works.id"), nullable=True)
    status = Column(String(15), nullable=False, default="pending")
    amount_reimbursed = Column(Numeric(14, 2), nullable=False, default=0)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    subcategory_id = Column(Integer, ForeignKey("transaction_subcategories.id"), nullable=True)
    partner_id = Column(Integer, ForeignKey("partners.id"), nullable=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class MoneyTransfer(Base):
    __tablename__ = "money_transfers"
    __table_args__ = {"extend_existing": True}
    id = Column(Integer, primary_key=True)
    operator = Column(String(20), nullable=False)
    reference_number = Column(String(50), nullable=True)
    sender_name = Column(String(150), nullable=False)
    receiver_name = Column(String(150), nullable=False)
    sender_id = Column(Integer, nullable=True)
    receiver_id = Column(Integer, nullable=True)
    amount = Column(Numeric(14, 2), nullable=False)
    commission_transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=True)
    main_transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=True)
    direction = Column(String(10), nullable=False)
    delegacion_origin = Column(String(10), nullable=True)
    delegacion_dest = Column(String(10), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)