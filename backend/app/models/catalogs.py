"""
Modelos de catálogos — M4.
Proyectos, obras, categorías, subcategorías, proveedores,
empleados, socios, cuentas corporativas y vehículos.
"""

from sqlalchemy import (
    Column, Integer, String, Text, Boolean, Numeric,
    Date, DateTime, ForeignKey, UniqueConstraint, CheckConstraint,
    func,
)
from sqlalchemy.orm import relationship
from app.database import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True)
    code = Column(String(30), unique=True, nullable=False)
    name = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())

    works = relationship("Work", back_populates="project")


class Work(Base):
    __tablename__ = "works"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    code = Column(String(50), nullable=False)
    name = Column(String(150), nullable=False)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())

    project = relationship("Project", back_populates="works")

    __table_args__ = (
        UniqueConstraint("project_id", "code", name="uq_work_project_code"),
    )


class TransactionCategory(Base):
    __tablename__ = "transaction_categories"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    type = Column(String(10), nullable=False)
    requires_attachment = Column(Boolean, default=True)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())

    subcategories = relationship("TransactionSubcategory", back_populates="category")

    __table_args__ = (
        CheckConstraint("type IN ('income','expense','both')", name="ck_category_type"),
    )


class TransactionSubcategory(Base):
    __tablename__ = "transaction_subcategories"

    id = Column(Integer, primary_key=True)
    category_id = Column(Integer, ForeignKey("transaction_categories.id"), nullable=False)
    name = Column(String(100), nullable=False)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())

    category = relationship("TransactionCategory", back_populates="subcategories")

    __table_args__ = (
        UniqueConstraint("category_id", "name", name="uq_subcategory_category_name"),
    )


class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True)
    code = Column(String(30), unique=True, nullable=False)
    name = Column(String(150), nullable=False)
    supplier_type = Column(String(20), nullable=False)
    tax_id = Column(String(50), nullable=True)
    contact_name = Column(String(100), nullable=True)
    phone = Column(String(30), nullable=True)
    email = Column(String(150), nullable=True)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        CheckConstraint(
            "supplier_type IN ('empresa','organismo','aerolinea','gasolinera','banco','otro')",
            name="ck_supplier_type"
        ),
    )


class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True)
    code = Column(String(30), unique=True, nullable=False)
    full_name = Column(String(100), nullable=False)
    department = Column(String(100), nullable=True)
    position = Column(String(100), nullable=True)
    delegacion = Column(String(10), nullable=False)
    salary_gross = Column(Numeric(12, 2), nullable=False, default=0)
    salary_transfer = Column(Numeric(12, 2), nullable=False, default=0)
    salary_effective_date = Column(Date, nullable=False)
    advance_pending = Column(Boolean, default=False)
    advance_amount = Column(Numeric(12, 2), nullable=True)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        CheckConstraint("delegacion IN ('Bata','Malabo')", name="ck_employee_delegacion"),
    )


class EmployeeSalaryHistory(Base):
    __tablename__ = "employee_salary_history"

    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    salary_gross = Column(Numeric(12, 2), nullable=False)
    salary_transfer = Column(Numeric(12, 2), nullable=False)
    effective_date = Column(Date, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())


class Partner(Base):
    __tablename__ = "partners"

    id = Column(Integer, primary_key=True)
    code = Column(String(10), unique=True, nullable=False)
    full_name = Column(String(100), nullable=False)
    participation_pct = Column(Numeric(5, 2), nullable=False)
    can_contribute = Column(Boolean, default=False)
    current_balance = Column(Numeric(14, 2), nullable=False, default=0)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())


class CorporateAccount(Base):
    __tablename__ = "corporate_accounts"

    id = Column(Integer, primary_key=True)
    bank_name = Column(String(100), nullable=False)
    account_number = Column(String(50), nullable=False)
    account_holder = Column(String(100), nullable=False)
    delegacion = Column(String(10), nullable=False)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        CheckConstraint("delegacion IN ('Bata','Malabo')", name="ck_corpaccount_delegacion"),
    )


class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(Integer, primary_key=True)
    plate = Column(String(20), unique=True, nullable=False)
    brand = Column(String(50), nullable=True)
    model = Column(String(50), nullable=True)
    year = Column(Integer, nullable=True)
    delegacion = Column(String(10), nullable=False)
    usual_driver_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        CheckConstraint("delegacion IN ('Bata','Malabo')", name="ck_vehicle_delegacion"),
    )

# M9: Re-export de modelos financieros especiales (Capa 2)
from app.models.financial_modules import (
    AdvanceLoan, RetentionDeposit, Float, FloatJustification,
    InstallmentPayment, InstallmentRecord, CurrencyOperation, EurStock,
    PartnerAccountMovement, ReimbursableExpense, MoneyTransfer,
)

# M9: Re-export adicional — CashSession/Transaction desde cash_flow
# Los servicios M9 (financial_helpers.py + 8 _service.py) usan el patrón
# `from app.models import catalogs as m; m.CashSession`. En este proyecto
# CashSession/Transaction/TransactionProject viven en app.models.cash_flow,
# así que los re-exportamos aquí para mantener el patrón M9 sin tocar los
# servicios.
from app.models.cash_flow import CashSession, Transaction, TransactionProject
