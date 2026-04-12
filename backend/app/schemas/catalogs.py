"""
Módulo 4 — Schemas Pydantic para todos los catálogos.
Cada catálogo tiene schemas de creación, actualización y respuesta.
Los schemas de respuesta incluyen relaciones relevantes (ej: obras con su proyecto).
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal


# ─────────────────────────────────────────────
# PROYECTOS
# ─────────────────────────────────────────────

class ProjectCreate(BaseModel):
    code: str = Field(..., min_length=1, max_length=30)
    name: str = Field(..., min_length=1, max_length=150)
    description: Optional[str] = None

class ProjectUpdate(BaseModel):
    code: Optional[str] = Field(None, min_length=1, max_length=30)
    name: Optional[str] = Field(None, min_length=1, max_length=150)
    description: Optional[str] = None
    active: Optional[bool] = None

class ProjectResponse(BaseModel):
    id: int
    code: str
    name: str
    description: Optional[str]
    active: bool
    created_at: datetime
    works_count: int = 0

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────
# OBRAS
# ─────────────────────────────────────────────

class WorkCreate(BaseModel):
    project_id: int
    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=150)

class WorkCreateInline(BaseModel):
    """Creación al vuelo desde el formulario de transacciones."""
    project_id: int
    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=150)

class WorkUpdate(BaseModel):
    code: Optional[str] = Field(None, min_length=1, max_length=50)
    name: Optional[str] = Field(None, min_length=1, max_length=150)
    active: Optional[bool] = None

class WorkResponse(BaseModel):
    id: int
    project_id: int
    project_code: Optional[str] = None
    project_name: Optional[str] = None
    code: str
    name: str
    active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────
# CATEGORÍAS
# ─────────────────────────────────────────────

class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    type: str = Field(..., pattern=r'^(income|expense|both)$')
    requires_attachment: bool = True

class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    type: Optional[str] = Field(None, pattern=r'^(income|expense|both)$')
    requires_attachment: Optional[bool] = None
    active: Optional[bool] = None

class CategoryResponse(BaseModel):
    id: int
    name: str
    type: str
    requires_attachment: bool
    active: bool
    created_at: datetime
    subcategories_count: int = 0

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────
# SUBCATEGORÍAS
# ─────────────────────────────────────────────

class SubcategoryCreate(BaseModel):
    category_id: int
    name: str = Field(..., min_length=1, max_length=100)

class SubcategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    active: Optional[bool] = None

class SubcategoryResponse(BaseModel):
    id: int
    category_id: int
    category_name: Optional[str] = None
    name: str
    active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────
# PROVEEDORES
# ─────────────────────────────────────────────

class SupplierCreate(BaseModel):
    code: str = Field(..., min_length=1, max_length=30)
    name: str = Field(..., min_length=1, max_length=150)
    supplier_type: str = Field(..., pattern=r'^(empresa|organismo|aerolinea|gasolinera|banco|otro)$')
    tax_id: Optional[str] = Field(None, max_length=50)
    contact_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=30)
    email: Optional[str] = Field(None, max_length=150)

class SupplierUpdate(BaseModel):
    code: Optional[str] = Field(None, min_length=1, max_length=30)
    name: Optional[str] = Field(None, min_length=1, max_length=150)
    supplier_type: Optional[str] = Field(None, pattern=r'^(empresa|organismo|aerolinea|gasolinera|banco|otro)$')
    tax_id: Optional[str] = Field(None, max_length=50)
    contact_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=30)
    email: Optional[str] = Field(None, max_length=150)
    active: Optional[bool] = None

class SupplierResponse(BaseModel):
    id: int
    code: str
    name: str
    supplier_type: str
    tax_id: Optional[str]
    contact_name: Optional[str]
    phone: Optional[str]
    email: Optional[str]
    active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────
# EMPLEADOS
# ─────────────────────────────────────────────

class EmployeeCreate(BaseModel):
    code: str = Field(..., min_length=1, max_length=30)
    full_name: str = Field(..., min_length=1, max_length=100)
    department: Optional[str] = Field(None, max_length=100)
    position: Optional[str] = Field(None, max_length=100)
    delegacion: str = Field(..., pattern=r'^(Bata|Malabo)$')
    salary_gross: Decimal = Field(default=Decimal("0"))
    salary_transfer: Decimal = Field(default=Decimal("0"))
    salary_effective_date: date

class EmployeeUpdate(BaseModel):
    code: Optional[str] = Field(None, min_length=1, max_length=30)
    full_name: Optional[str] = Field(None, min_length=1, max_length=100)
    department: Optional[str] = Field(None, max_length=100)
    position: Optional[str] = Field(None, max_length=100)
    delegacion: Optional[str] = Field(None, pattern=r'^(Bata|Malabo)$')
    active: Optional[bool] = None

class EmployeeSalaryUpdate(BaseModel):
    """Actualización de salario — genera registro en employee_salary_history."""
    salary_gross: Decimal = Field(..., ge=0)
    salary_transfer: Decimal = Field(..., ge=0)
    salary_effective_date: date

class EmployeeResponse(BaseModel):
    id: int
    code: str
    full_name: str
    department: Optional[str]
    position: Optional[str]
    delegacion: str
    salary_gross: Optional[Decimal] = None  # Solo visible para admin y contable
    salary_transfer: Optional[Decimal] = None  # Solo visible para admin y contable
    salary_effective_date: Optional[date] = None
    advance_pending: bool
    advance_amount: Optional[Decimal]
    active: bool
    created_at: datetime

    model_config = {"from_attributes": True}

class SalaryHistoryResponse(BaseModel):
    id: int
    employee_id: int
    salary_gross: Decimal
    salary_transfer: Decimal
    effective_date: date
    created_by: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────
# SOCIOS
# ─────────────────────────────────────────────

class PartnerCreate(BaseModel):
    code: str = Field(..., min_length=1, max_length=10)
    full_name: str = Field(..., min_length=1, max_length=100)
    participation_pct: Decimal = Field(..., ge=0, le=100)
    can_contribute: bool = False

class PartnerUpdate(BaseModel):
    code: Optional[str] = Field(None, min_length=1, max_length=10)
    full_name: Optional[str] = Field(None, min_length=1, max_length=100)
    participation_pct: Optional[Decimal] = Field(None, ge=0, le=100)
    can_contribute: Optional[bool] = None
    active: Optional[bool] = None

class PartnerResponse(BaseModel):
    id: int
    code: str
    full_name: str
    participation_pct: Decimal
    can_contribute: bool
    current_balance: Optional[Decimal] = None  # Solo visible para admin y contable
    active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────
# CUENTAS CORPORATIVAS
# ─────────────────────────────────────────────

class CorporateAccountCreate(BaseModel):
    bank_name: str = Field(..., min_length=1, max_length=100)
    account_number: str = Field(..., min_length=1, max_length=50)
    account_holder: str = Field(..., min_length=1, max_length=100)
    delegacion: str = Field(..., pattern=r'^(Bata|Malabo)$')

class CorporateAccountUpdate(BaseModel):
    bank_name: Optional[str] = Field(None, min_length=1, max_length=100)
    account_number: Optional[str] = Field(None, min_length=1, max_length=50)
    account_holder: Optional[str] = Field(None, min_length=1, max_length=100)
    delegacion: Optional[str] = Field(None, pattern=r'^(Bata|Malabo)$')
    active: Optional[bool] = None

class CorporateAccountResponse(BaseModel):
    id: int
    bank_name: str
    account_number: str
    account_holder: str
    delegacion: str
    active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────
# VEHÍCULOS DE FLOTA
# ─────────────────────────────────────────────

class VehicleCreate(BaseModel):
    plate: str = Field(..., min_length=1, max_length=20)
    brand: Optional[str] = Field(None, max_length=50)
    model: Optional[str] = Field(None, max_length=50)
    year: Optional[int] = None
    delegacion: str = Field(..., pattern=r'^(Bata|Malabo)$')
    usual_driver_id: Optional[int] = None

class VehicleUpdate(BaseModel):
    plate: Optional[str] = Field(None, min_length=1, max_length=20)
    brand: Optional[str] = Field(None, max_length=50)
    model: Optional[str] = Field(None, max_length=50)
    year: Optional[int] = None
    delegacion: Optional[str] = Field(None, pattern=r'^(Bata|Malabo)$')
    usual_driver_id: Optional[int] = None
    active: Optional[bool] = None

class VehicleResponse(BaseModel):
    id: int
    plate: str
    brand: Optional[str]
    model: Optional[str]
    year: Optional[int]
    delegacion: str
    usual_driver_id: Optional[int]
    usual_driver_name: Optional[str] = None
    active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────
# PAGINACIÓN GENÉRICA
# ─────────────────────────────────────────────

class PaginatedResponse(BaseModel):
    items: list
    total: int
    page: int
    page_size: int
    pages: int
