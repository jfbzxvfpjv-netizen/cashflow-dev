"""
Schemas — Sesiones de caja.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class CashSessionRead(BaseModel):
    id: int
    user_id: int
    delegacion: str
    opened_at: datetime
    closed_at: Optional[datetime] = None
    opening_balance: float
    closing_balance: Optional[float] = None
    status: str
    notes: Optional[str] = None
    user_full_name: Optional[str] = None
    transaction_count: Optional[int] = None
    total_income: Optional[float] = None
    total_expense: Optional[float] = None
    model_config = {"from_attributes": True}


class CashSessionOpen(BaseModel):
    delegacion: Optional[str] = Field(None, pattern=r"^(Bata|Malabo)$")
    notes: Optional[str] = Field(None, max_length=500)


class CashSessionClose(BaseModel):
    notes: Optional[str] = Field(None, max_length=500)


class CashSessionFilters(BaseModel):
    delegacion: Optional[str] = None
    user_id: Optional[int] = None
    status: Optional[str] = None
    date_start: Optional[datetime] = None
    date_end: Optional[datetime] = None
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
