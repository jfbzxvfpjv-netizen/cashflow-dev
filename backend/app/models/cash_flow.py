"""
Modelos M5 — system_config, cash_sessions, bank_withdrawal_requests.
Modelos M6 (estructura) — transactions, transaction_attachments, transaction_signatures,
    transaction_projects, accounting_periods.
Se crean automáticamente vía Base.metadata.create_all().
"""
from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Numeric, Boolean, Text, Date,
    DateTime, ForeignKey, CheckConstraint, UniqueConstraint,
    JSON,
)
from sqlalchemy.orm import relationship
from app.database import Base


# ── system_config ────────────────────────────────────────────────────────────

class SystemConfig(Base):
    __tablename__ = "system_config"

    id = Column(Integer, primary_key=True, index=True)
    delegacion = Column(String(10), unique=True, nullable=False)
    opening_balance = Column(Numeric(14, 2), nullable=False, default=0)
    opening_balance_date = Column(Date, nullable=False)
    currency = Column(String(5), default="XAF")
    organization_name = Column(String(150), nullable=False)
    configured_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    configured_at = Column(DateTime, default=datetime.utcnow)
    last_modified_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    last_modified_at = Column(DateTime, nullable=True)

    __table_args__ = (
        CheckConstraint("delegacion IN ('Bata','Malabo')", name="ck_sysconfig_deleg"),
    )


# ── cash_sessions ───────────────────────────────────────────────────────────

class CashSession(Base):
    __tablename__ = "cash_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    delegacion = Column(String(10), nullable=False)
    opened_at = Column(DateTime, default=datetime.utcnow)
    closed_at = Column(DateTime, nullable=True)
    opening_balance = Column(Numeric(12, 2), nullable=False, default=0)
    closing_balance = Column(Numeric(12, 2), nullable=True)
    status = Column(String(10), default="open")
    notes = Column(Text, nullable=True)

    user = relationship("User", foreign_keys=[user_id])

    __table_args__ = (
        CheckConstraint("status IN ('open','closed')", name="ck_session_status"),
        CheckConstraint("delegacion IN ('Bata','Malabo')", name="ck_session_deleg"),
    )


# ── bank_withdrawal_requests ────────────────────────────────────────────────

class BankWithdrawalRequest(Base):
    __tablename__ = "bank_withdrawal_requests"

    id = Column(Integer, primary_key=True, index=True)
    delegacion = Column(String(10), nullable=False)
    corporate_account_id = Column(Integer, ForeignKey("corporate_accounts.id"), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    cheque_reference = Column(String(100), nullable=False)
    proposed_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    proposed_at = Column(DateTime, default=datetime.utcnow)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    confirmed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    confirmed_at = Column(DateTime, nullable=True)
    session_id = Column(Integer, ForeignKey("cash_sessions.id"), nullable=True)
    status = Column(String(15), default="pending")
    rejection_reason = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)

    corporate_account = relationship("CorporateAccount", foreign_keys=[corporate_account_id])

    __table_args__ = (
        CheckConstraint("status IN ('pending','approved','confirmed','rejected')", name="ck_bw_status"),
        CheckConstraint("amount > 0", name="ck_bw_amount_pos"),
    )


# ── accounting_periods ──────────────────────────────────────────────────────

class AccountingPeriod(Base):
    __tablename__ = "accounting_periods"

    id = Column(Integer, primary_key=True, index=True)
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    delegacion = Column(String(10), nullable=False)
    closed_at = Column(DateTime, default=datetime.utcnow)
    closed_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    total_income = Column(Numeric(14, 2), nullable=False)
    total_expense = Column(Numeric(14, 2), nullable=False)
    net_balance = Column(Numeric(14, 2), nullable=False)
    transaction_count = Column(Integer, nullable=False)
    notes = Column(Text, nullable=True)

    __table_args__ = (
        UniqueConstraint("year", "month", "delegacion", name="uq_acct_period"),
        CheckConstraint("month BETWEEN 1 AND 12", name="ck_acct_month"),
    )


# ── transactions ────────────────────────────────────────────────────────────

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("cash_sessions.id"), nullable=False)
    delegacion = Column(String(10), nullable=False)
    category_id = Column(Integer, ForeignKey("transaction_categories.id"), nullable=False)
    subcategory_id = Column(Integer, ForeignKey("transaction_subcategories.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    partner_id = Column(Integer, ForeignKey("partners.id"), nullable=True)
    counterparty_free = Column(String(150), nullable=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=True)
    type = Column(String(10), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    concept = Column(Text, nullable=False)
    reference_number = Column(String(10), unique=True, nullable=False)
    transaction_type = Column(String(20), default="normal")
    cancelled = Column(Boolean, default=False)
    cancel_ref_id = Column(Integer, ForeignKey("transactions.id"), nullable=True)
    is_adjustment = Column(Boolean, default=False)
    adjustment_ref_period = Column(Integer, ForeignKey("accounting_periods.id"), nullable=True)
    approval_status = Column(String(15), default="approved")
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    imported = Column(Boolean, default=False)
    import_source = Column(String(255), nullable=True)
    imported_editable_until = Column(DateTime, nullable=True)
    editable_until = Column(DateTime, nullable=False)
    integrity_hash = Column(String(64), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("CashSession", foreign_keys=[session_id])
    category = relationship("TransactionCategory", foreign_keys=[category_id])
    subcategory = relationship("TransactionSubcategory", foreign_keys=[subcategory_id])

    __table_args__ = (
        CheckConstraint("type IN ('income','expense')", name="ck_tx_type"),
        CheckConstraint("amount > 0", name="ck_tx_amount_pos"),
        CheckConstraint("approval_status IN ('approved','pending_approval','rejected')", name="ck_tx_approval"),
    )


# ── transaction_projects ────────────────────────────────────────────────────

class TransactionProject(Base):
    __tablename__ = "transaction_projects"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    work_id = Column(Integer, ForeignKey("works.id"), nullable=True)

    __table_args__ = (
        UniqueConstraint("transaction_id", "project_id", "work_id", name="uq_tx_proj_work"),
    )


# ── transaction_attachments ─────────────────────────────────────────────────

class TransactionAttachment(Base):
    __tablename__ = "transaction_attachments"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=False)
    original_filename = Column(String(255), nullable=False)
    stored_filename = Column(String(255), nullable=False)
    mime_type = Column(String(100), nullable=True)
    file_size_bytes = Column(Integer, nullable=True)
    file_path = Column(String(500), nullable=False)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    locked = Column(Boolean, default=False)


# ── transaction_signatures ──────────────────────────────────────────────────

class TransactionSignature(Base):
    __tablename__ = "transaction_signatures"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=False)
    signer_type = Column(String(20), nullable=False)
    signer_name = Column(String(100), nullable=False)
    signature_data = Column(Text, nullable=False)
    signed_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("transaction_id", "signer_type", name="uq_tx_signer"),
    )
