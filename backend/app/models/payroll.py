"""
M10b — Nóminas mensuales.

Tablas:
- payroll_periods: 1 por (mes, año, delegación). Status 'draft'|'paid'.
- payroll_entries: 1 por (periodo, empleado). Snapshot de salarios al generar.
"""
from sqlalchemy import (
    Column, Integer, SmallInteger, String, Numeric, DateTime, Date,
    Text, ForeignKey, CheckConstraint, UniqueConstraint,
)
from sqlalchemy.orm import relationship
from app.models.cash_flow import Base
from datetime import datetime


class PayrollPeriod(Base):
    __tablename__ = "payroll_periods"

    id          = Column(Integer, primary_key=True, index=True)
    year        = Column(SmallInteger, nullable=False)
    month       = Column(SmallInteger, nullable=False)
    delegacion  = Column(String(10), nullable=False)
    status      = Column(String(20), nullable=False, default="draft")
    created_by  = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at  = Column(DateTime, default=datetime.utcnow)
    paid_at     = Column(DateTime, nullable=True)
    notes       = Column(Text, nullable=True)

    entries = relationship("PayrollEntry", back_populates="period", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("month BETWEEN 1 AND 12", name="ck_payroll_month"),
        CheckConstraint("status IN ('draft','paid')", name="ck_payroll_status"),
        CheckConstraint("delegacion IN ('Bata','Malabo')", name="ck_payroll_deleg"),
        UniqueConstraint("year", "month", "delegacion", name="uq_payroll_year_month_deleg"),
    )


class PayrollEntry(Base):
    __tablename__ = "payroll_entries"

    id              = Column(Integer, primary_key=True, index=True)
    period_id       = Column(Integer, ForeignKey("payroll_periods.id", ondelete="CASCADE"), nullable=False)
    employee_id     = Column(Integer, ForeignKey("employees.id"), nullable=False)
    salary_gross    = Column(Numeric(12, 2), nullable=False)
    salary_transfer = Column(Numeric(12, 2), nullable=False)
    cash_amount     = Column(Numeric(12, 2), nullable=False)
    transaction_id  = Column(Integer, ForeignKey("transactions.id"), nullable=True)
    paid_at         = Column(DateTime, nullable=True)
    notes           = Column(Text, nullable=True)

    period = relationship("PayrollPeriod", back_populates="entries")

    __table_args__ = (
        UniqueConstraint("period_id", "employee_id", name="uq_payroll_entry_period_employee"),
        CheckConstraint("cash_amount >= 0", name="ck_payroll_entry_amounts"),
    )
