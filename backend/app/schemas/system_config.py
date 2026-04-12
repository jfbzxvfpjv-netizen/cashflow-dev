"""
Schemas — Configuración del sistema (saldo inicial por delegación).
"""
from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class SystemConfigRead(BaseModel):
    id: int
    delegacion: str
    opening_balance: float
    opening_balance_date: date
    currency: str
    organization_name: str
    configured_by: int
    configured_at: datetime
    last_modified_by: Optional[int] = None
    last_modified_at: Optional[datetime] = None
    model_config = {"from_attributes": True}


class SystemConfigCreate(BaseModel):
    delegacion: str = Field(..., pattern=r"^(Bata|Malabo)$")
    opening_balance: float = Field(..., ge=0)
    opening_balance_date: date
    organization_name: str = Field(..., min_length=2, max_length=150)

    @field_validator("opening_balance_date")
    @classmethod
    def no_futura(cls, v):
        if v > date.today():
            raise ValueError("La fecha no puede ser posterior a hoy")
        return v


class SystemConfigUpdate(BaseModel):
    opening_balance: Optional[float] = Field(None, ge=0)
    opening_balance_date: Optional[date] = None
    organization_name: Optional[str] = Field(None, min_length=2, max_length=150)

    @field_validator("opening_balance_date")
    @classmethod
    def no_futura(cls, v):
        if v is not None and v > date.today():
            raise ValueError("La fecha no puede ser posterior a hoy")
        return v
