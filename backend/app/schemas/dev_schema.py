"""
Schemas para el módulo de reset y fixtures de desarrollo.
"""
from pydantic import BaseModel


class ConfirmAction(BaseModel):
    confirm: str


class DevResult(BaseModel):
    action: str
    message: str
    details: dict = {}


class EnvInfo(BaseModel):
    env: str
