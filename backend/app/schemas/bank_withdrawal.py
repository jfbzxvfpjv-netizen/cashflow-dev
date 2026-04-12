"""
Schemas — Retiradas bancarias (flujo Contable → Admin → Gestor).
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class BankWithdrawalRead(BaseModel):
    id: int
    delegacion: str
    corporate_account_id: int
    amount: float
    cheque_reference: str
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
    proposed_by_name: Optional[str] = None
    approved_by_name: Optional[str] = None
    confirmed_by_name: Optional[str] = None
    account_bank_name: Optional[str] = None
    account_number: Optional[str] = None
    model_config = {"from_attributes": True}


class BankWithdrawalCreate(BaseModel):
    delegacion: str = Field(..., pattern=r"^(Bata|Malabo)$")
    corporate_account_id: int = Field(..., gt=0)
    amount: float = Field(..., gt=0)
    cheque_reference: str = Field(..., min_length=1, max_length=100)
    notes: Optional[str] = Field(None, max_length=500)


class BankWithdrawalApprove(BaseModel):
    notes: Optional[str] = Field(None, max_length=500)


class BankWithdrawalReject(BaseModel):
    rejection_reason: str = Field(..., min_length=5, max_length=500)


class BankWithdrawalConfirm(BaseModel):
    notes: Optional[str] = Field(None, max_length=500)


class BankWithdrawalFilters(BaseModel):
    delegacion: Optional[str] = None
    status: Optional[str] = None
    date_start: Optional[datetime] = None
    date_end: Optional[datetime] = None
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
