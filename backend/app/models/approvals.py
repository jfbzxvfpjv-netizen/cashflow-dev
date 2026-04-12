"""
Módulo 6 — Modelos de aprobaciones por umbral y arqueos de caja.
CategoryApprovalThreshold define el importe a partir del cual una transacción
requiere aprobación del Administrador. ExpenseApproval registra cada solicitud.
CashCount almacena los arqueos de caja.
"""
from sqlalchemy import Column, Integer, String, Numeric, DateTime, Text, ForeignKey, func
from app.database import Base


class CategoryApprovalThreshold(Base):
    """Umbral configurable por categoría y delegación."""
    __tablename__ = "category_approval_thresholds"

    id = Column(Integer, primary_key=True, autoincrement=True)
    category_id = Column(Integer, ForeignKey("transaction_categories.id"), nullable=False)
    delegacion = Column(String(10), nullable=False)
    threshold_amount = Column(Numeric(12, 2), nullable=False)
    created_at = Column(DateTime, server_default=func.now())


class ExpenseApproval(Base):
    """Registro de aprobación/rechazo de transacciones que superan el umbral."""
    __tablename__ = "expense_approvals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=False)
    requested_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    requested_at = Column(DateTime, server_default=func.now())
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    status = Column(String(15), nullable=False, default="pending")  # pending, approved, rejected
    rejection_reason = Column(Text, nullable=True)


class CashCount(Base):
    """Arqueo de caja — comparación entre saldo teórico y conteo físico."""
    __tablename__ = "cash_counts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("cash_sessions.id"), nullable=False)
    delegacion = Column(String(10), nullable=False)
    theoretical_balance = Column(Numeric(14, 2), nullable=False)
    physical_count = Column(Numeric(14, 2), nullable=False)
    difference = Column(Numeric(14, 2), nullable=False)
    notes = Column(Text, nullable=True)
    counted_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    counted_at = Column(DateTime, server_default=func.now())
