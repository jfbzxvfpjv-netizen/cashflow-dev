"""
Router — /config — Configuración del saldo inicial.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.deps import get_db, get_current_user, require_role
from app.models.user import User
from app.schemas.system_config import SystemConfigRead, SystemConfigCreate, SystemConfigUpdate
from app.services.config_service import ConfigService

router = APIRouter(prefix="/config", tags=["Configuración"])


@router.get("", response_model=List[SystemConfigRead])
async def list_config(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    svc = ConfigService(db)
    configs = svc.get_all()
    if user.role == "gestor":
        configs = [c for c in configs if c.delegacion == user.delegacion]
    return configs


@router.get("/balance/{delegacion}")
async def get_balance(delegacion: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if user.role == "gestor" and user.delegacion != delegacion:
        raise HTTPException(status_code=403, detail="Solo puede consultar su delegación")
    return {"delegacion": delegacion, "current_balance": ConfigService(db).get_current_balance(delegacion)}


@router.post("", response_model=SystemConfigRead, status_code=201)
async def create_config(data: SystemConfigCreate, db: Session = Depends(get_db),
                        user: User = Depends(require_role("admin"))):
    return ConfigService(db).create(data, user)


@router.put("/{delegacion}", response_model=SystemConfigRead)
async def update_config(delegacion: str, data: SystemConfigUpdate, db: Session = Depends(get_db),
                        user: User = Depends(require_role("admin"))):
    return ConfigService(db).update(delegacion, data, user)
