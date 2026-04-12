"""
Esquemas Pydantic — Autenticación.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=1)


class UserBasicResponse(BaseModel):
    id: int
    username: str
    full_name: str
    role: str
    delegacion: str
    active: bool
    last_login: Optional[datetime] = None
    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserBasicResponse


class LogoutResponse(BaseModel):
    message: str = "Sesión cerrada correctamente."
