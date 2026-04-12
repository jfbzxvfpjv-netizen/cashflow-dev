"""
Módulo 6 — Schemas Pydantic para transacciones.
Incluye creación, actualización, listado con filtros, detalle con estado de edición
y respuestas paginadas.
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
from decimal import Decimal


# --- Creación de transacción ---

class TransactionProjectIn(BaseModel):
    """Asignación de proyecto y obra a una transacción."""
    project_id: int
    work_id: int


class TransactionCreate(BaseModel):
    """Payload para registrar una transacción nueva."""
    category_id: int
    subcategory_id: int
    type: str = Field(..., pattern="^(income|expense)$")
    amount: Decimal = Field(..., gt=0)
    concept: str = Field(..., min_length=3)
    projects: List[TransactionProjectIn] = Field(..., min_length=1)
    supplier_id: Optional[int] = None
    employee_id: Optional[int] = None
    partner_id: Optional[int] = None
    counterparty_free: Optional[str] = None
    vehicle_id: Optional[int] = None
    transaction_type: str = "normal"
    notes: Optional[str] = None

    @field_validator("counterparty_free")
    @classmethod
    def validate_counterparty(cls, v):
        if v is not None and len(v.strip().split()) < 2:
            raise ValueError("La contraparte libre debe tener al menos nombre y apellido")
        return v


class TransactionUpdate(BaseModel):
    """Campos editables dentro de la ventana de 15 minutos."""
    category_id: Optional[int] = None
    subcategory_id: Optional[int] = None
    type: Optional[str] = Field(None, pattern="^(income|expense)$")
    amount: Optional[Decimal] = Field(None, gt=0)
    concept: Optional[str] = Field(None, min_length=3)
    projects: Optional[List[TransactionProjectIn]] = None
    supplier_id: Optional[int] = None
    employee_id: Optional[int] = None
    partner_id: Optional[int] = None
    counterparty_free: Optional[str] = None
    vehicle_id: Optional[int] = None
    notes: Optional[str] = None


# --- Respuestas ---

class TransactionProjectOut(BaseModel):
    project_id: int
    work_id: int
    project_name: Optional[str] = None
    work_name: Optional[str] = None

    class Config:
        from_attributes = True


class TransactionOut(BaseModel):
    """Respuesta estándar de una transacción en listados."""
    id: int
    session_id: int
    delegacion: str
    category_id: int
    subcategory_id: int
    category_name: Optional[str] = None
    subcategory_name: Optional[str] = None
    user_id: int
    user_fullname: Optional[str] = None
    supplier_id: Optional[int] = None
    employee_id: Optional[int] = None
    partner_id: Optional[int] = None
    counterparty_free: Optional[str] = None
    vehicle_id: Optional[int] = None
    type: str
    amount: Decimal
    concept: str
    reference_number: str
    transaction_type: str
    cancelled: bool
    cancel_ref_id: Optional[int] = None
    is_adjustment: bool
    approval_status: str
    imported: bool
    integrity_hash: str
    created_at: datetime
    editable_until: datetime
    is_editable: Optional[bool] = False
    seconds_remaining: Optional[int] = 0
    has_attachments: Optional[bool] = False
    has_signatures: Optional[bool] = False
    projects: List[TransactionProjectOut] = []

    class Config:
        from_attributes = True


class TransactionDetail(TransactionOut):
    """Detalle completo de una transacción individual."""
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None
    imported_editable_until: Optional[datetime] = None
    import_source: Optional[str] = None
    adjustment_ref_period: Optional[int] = None
    notes: Optional[str] = None


class TransactionListResponse(BaseModel):
    """Respuesta paginada del listado de transacciones."""
    items: List[TransactionOut]
    total: int
    page: int
    page_size: int
    pages: int


# --- Cancelación ---

class CancelRequest(BaseModel):
    """Motivo obligatorio para cancelar una transacción."""
    reason: str = Field(..., min_length=3)


# --- Aprobación / Rechazo ---

class RejectRequest(BaseModel):
    """Motivo obligatorio para rechazar una transacción."""
    reason: str = Field(..., min_length=3)
