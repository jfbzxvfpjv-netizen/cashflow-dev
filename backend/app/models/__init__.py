"""
Paquete models — Importa todos los modelos para registro en SQLAlchemy.
"""

from app.models.user import User
from app.models.audit_log import AuditLog
from app.models.catalogs import (
    Project, Work,
    TransactionCategory, TransactionSubcategory,
    Supplier, Employee, EmployeeSalaryHistory,
    Partner, CorporateAccount, Vehicle,
)

__all__ = [
    "User", "AuditLog",
    "Project", "Work",
    "TransactionCategory", "TransactionSubcategory",
    "Supplier", "Employee", "EmployeeSalaryHistory",
    "Partner", "CorporateAccount", "Vehicle",
]

# M5 — Sesiones, configuración, retiradas + estructura transacciones
from app.models.cash_flow import (
    SystemConfig, CashSession, BankWithdrawalRequest,
    AccountingPeriod, Transaction, TransactionProject,
    TransactionAttachment, TransactionSignature,
)

__all__ += [
    "SystemConfig", "CashSession", "BankWithdrawalRequest",
    "AccountingPeriod", "Transaction", "TransactionProject",
    "TransactionAttachment", "TransactionSignature",
]

# --- M6: Aprobaciones y arqueos ---
from app.models.approvals import CategoryApprovalThreshold, ExpenseApproval, CashCount

from app.models.import_history import ImportHistory
__all__ += ["ImportHistory"]
