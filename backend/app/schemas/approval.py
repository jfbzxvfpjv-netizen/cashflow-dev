"""
Módulo 6 — Schemas Pydantic para umbrales de aprobación.
"""
from pydantic import BaseModel, Field
from typing import Optional
from decimal import Decimal
from datetime import datetime


class ThresholdCreate(BaseModel):
    category_id: int
    delegacion: str = Field(..., pattern="^(Bata|Malabo)$")
    threshold_amount: Decimal = Field(..., gt=0)


class ThresholdUpdate(BaseModel):
    threshold_amount: Decimal = Field(..., gt=0)


class ThresholdOut(BaseModel):
    id: int
    category_id: int
    category_name: Optional[str] = None
    delegacion: str
    threshold_amount: Decimal
    created_at: datetime

    class Config:
        from_attributes = True


class ApprovalOut(BaseModel):
    id: int
    transaction_id: int
    reference_number: Optional[str] = None
    concept: Optional[str] = None
    amount: Optional[Decimal] = None
    requested_by: int
    requested_at: datetime
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None
    status: str
    rejection_reason: Optional[str] = None

    class Config:
        from_attributes = True
