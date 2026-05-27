"""
Schemas — Retiradas bancarias (flujo 4 pasos: Gestor solicita -> Contable formaliza -> Admin aprueba -> Gestor confirma).
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, field_validator
from app.utils.text_utils import normalize_text, Field


class BankWithdrawalRead(BaseModel):
    id: int
    delegacion: str
    corporate_account_id: Optional[int] = None  # NULL hasta FORMALIZAR
    amount: float
    cheque_reference: Optional[str] = None  # NULL hasta FORMALIZAR

    # Flujo 4 pasos
    requested_by: Optional[int] = None
    requested_at: Optional[datetime] = None
    reason: Optional[str] = None
    formalized_by: Optional[int] = None
    formalized_at: Optional[datetime] = None

    # Backward compat (proposed_by = mismo que requested_by; mantenemos para no romper)
    proposed_by: int
    proposed_at: datetime

    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None
    confirmed_by: Optional[int] = None
    confirmed_at: Optional[datetime] = None
    session_id: Optional[int] = None
    status: str
    rejection_reason: Optional[str] = None
    notes: Optional[str] = None

    # Nombres derivados (rellenados por enrich)
    requested_by_name: Optional[str] = None
    formalized_by_name: Optional[str] = None
    proposed_by_name: Optional[str] = None
    approved_by_name: Optional[str] = None
    confirmed_by_name: Optional[str] = None
    account_bank_name: Optional[str] = None
    account_number: Optional[str] = None

    model_config = {"from_attributes": True}


class BankWithdrawalRequestCreate(BaseModel):
    """Paso 1: gestor SOLICITA. Solo importe y motivo."""
    delegacion: str = Field(..., pattern=r"^(Bata|Malabo)$")
    amount: float = Field(..., gt=0)
    reason: str = Field(..., min_length=5, max_length=500)
    notes: Optional[str] = Field(None, max_length=500)
    @field_validator('reason', mode='before')
    @classmethod
    def _norm_reason(cls, v):
        return normalize_text(v) if v else v

class BankWithdrawalFormalize(BaseModel):
    """Paso 2: contable FORMALIZA (añade cuenta + cheque tras visita al banco)."""
    corporate_account_id: int = Field(..., gt=0)
    cheque_reference: str = Field(..., min_length=1, max_length=100)
    notes: Optional[str] = Field(None, max_length=500)


class BankWithdrawalApprove(BaseModel):
    """Paso 3a: admin APRUEBA."""
    notes: Optional[str] = Field(None, max_length=500)


class BankWithdrawalReject(BaseModel):
    """Paso 3b: admin RECHAZA (puede ocurrir desde requested o formalized)."""
    rejection_reason: str = Field(..., min_length=5, max_length=500)
    @field_validator('reason', mode='before')
    @classmethod
    def _norm_reason(cls, v):
        return normalize_text(v) if v else v
    @field_validator('rejection_reason', mode='before')
    @classmethod
    def _norm_rejection_reason(cls, v):
        return normalize_text(v) if v else v

class BankWithdrawalConfirm(BaseModel):
    """Paso 4: gestor CONFIRMA recepción física del dinero."""
    notes: Optional[str] = Field(None, max_length=500)


# Backward compat — código frontend/router antiguo que importe el nombre anterior
BankWithdrawalCreate = BankWithdrawalRequestCreate


class BankWithdrawalFilters(BaseModel):
    delegacion: Optional[str] = None
    status: Optional[str] = None
    date_start: Optional[datetime] = None
    date_end: Optional[datetime] = None
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
