"""
Schemas M10b — Nóminas.
"""
from datetime import datetime
from typing import Optional, List
from decimal import Decimal
from pydantic import BaseModel, Field


class PayrollPeriodCreate(BaseModel):
    year: int = Field(..., ge=2020, le=2050)
    month: int = Field(..., ge=1, le=12)
    delegacion: str = Field(..., pattern=r"^(Bata|Malabo)$")
    notes: Optional[str] = Field(None, max_length=500)


class PayrollEntryRead(BaseModel):
    id: int
    employee_id: int
    employee_name: Optional[str] = None
    employee_code: Optional[str] = None
    salary_gross: Decimal
    salary_transfer: Decimal
    cash_amount: Decimal
    transaction_id: Optional[int] = None
    transaction_status: Optional[str] = None  # approval_status si transaction_id != None
    transaction_reference: Optional[str] = None
    paid_at: Optional[datetime] = None
    notes: Optional[str] = None
    model_config = {"from_attributes": True}


class PayrollPeriodRead(BaseModel):
    id: int
    year: int
    month: int
    delegacion: str
    status: str
    created_by: int
    created_by_name: Optional[str] = None
    created_at: datetime
    paid_at: Optional[datetime] = None
    notes: Optional[str] = None
    # Resumen
    total_employees: int = 0
    total_cash: Decimal = Decimal(0)
    paid_count: int = 0
    pending_count: int = 0
    model_config = {"from_attributes": True}


class PayrollPeriodDetail(PayrollPeriodRead):
    entries: List[PayrollEntryRead] = []


class PayrollEntryUpdate(BaseModel):
    cash_amount: Optional[Decimal] = Field(None, ge=0)
    notes: Optional[str] = Field(None, max_length=500)


class PayrollExecutePayload(BaseModel):
    """Lanzar pagos: lista opcional de entry_ids; si vacía, todas las pendientes del periodo."""
    entry_ids: Optional[List[int]] = None


class PayrollExecuteResult(BaseModel):
    paid: int
    pending_approval: int
    skipped: int
    errors: List[str] = []


class PayrollPayPayload(BaseModel):
    """Payload para pagar una entry individual: solo el bloque signature."""
    signature: dict  # ver TransactionSignatureCreate (signer_type, signature_method, etc.)


class PayrollPayResult(BaseModel):
    entry_id: int
    transaction_id: int
    transaction_reference: Optional[str] = None
    approval_status: str
