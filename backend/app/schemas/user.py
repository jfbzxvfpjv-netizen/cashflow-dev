"""
Esquemas Pydantic — Gestión de usuarios.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=2, max_length=100)
    role: str
    delegacion: str

    @field_validator("role")
    @classmethod
    def validate_role(cls, v):
        if v not in ("admin", "contable", "gestor", "consulta"):
            raise ValueError("Rol no válido. Valores: admin, contable, gestor, consulta")
        return v

    @field_validator("delegacion")
    @classmethod
    def validate_delegacion(cls, v):
        if v not in ("Bata", "Malabo", "Ambas"):
            raise ValueError("Delegación no válida. Valores: Bata, Malabo, Ambas")
        return v


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    role: Optional[str] = None
    delegacion: Optional[str] = None
    active: Optional[bool] = None

    @field_validator("role")
    @classmethod
    def validate_role(cls, v):
        if v is not None and v not in ("admin", "contable", "gestor", "consulta"):
            raise ValueError("Rol no válido.")
        return v

    @field_validator("delegacion")
    @classmethod
    def validate_delegacion(cls, v):
        if v is not None and v not in ("Bata", "Malabo", "Ambas"):
            raise ValueError("Delegación no válida.")
        return v


class PasswordChange(BaseModel):
    new_password: str = Field(..., min_length=8)


class PasswordChangeSelf(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)


class UserResponse(BaseModel):
    id: int
    username: str
    full_name: str
    role: str
    delegacion: str
    active: bool
    totp_enabled: bool
    last_login: Optional[datetime] = None
    created_at: datetime
    model_config = {"from_attributes": True}


class UserListResponse(BaseModel):
    items: list[UserResponse]
    total: int
    page: int
    page_size: int
