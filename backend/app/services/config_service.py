"""
Servicio — Configuración del sistema (saldo inicial por delegación).
"""
from datetime import datetime
from typing import Optional, List

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.cash_flow import SystemConfig, CashSession, Transaction
from app.models.user import User
from app.schemas.system_config import SystemConfigCreate, SystemConfigUpdate


class ConfigService:
    def __init__(self, db: Session):
        self.db = db

    def get_by_delegacion(self, delegacion: str) -> Optional[SystemConfig]:
        return self.db.query(SystemConfig).filter(SystemConfig.delegacion == delegacion).first()

    def get_all(self) -> List[SystemConfig]:
        return self.db.query(SystemConfig).all()

    def create(self, data: SystemConfigCreate, user: User) -> SystemConfig:
        self._require_admin(user)
        if self.get_by_delegacion(data.delegacion):
            raise HTTPException(status_code=409, detail=f"Ya existe configuración para {data.delegacion}")
        self._no_sessions(data.delegacion)

        config = SystemConfig(
            delegacion=data.delegacion, opening_balance=data.opening_balance,
            opening_balance_date=data.opening_balance_date, currency="XAF",
            organization_name=data.organization_name,
            configured_by=user.id, configured_at=datetime.utcnow(),
        )
        self.db.add(config)
        self.db.commit()
        self.db.refresh(config)
        return config

    def update(self, delegacion: str, data: SystemConfigUpdate, user: User) -> SystemConfig:
        self._require_admin(user)
        self._no_sessions(delegacion)
        config = self.get_by_delegacion(delegacion)
        if not config:
            raise HTTPException(status_code=404, detail=f"Sin configuración para {delegacion}")

        if data.opening_balance is not None:
            config.opening_balance = data.opening_balance
        if data.opening_balance_date is not None:
            config.opening_balance_date = data.opening_balance_date
        if data.organization_name is not None:
            config.organization_name = data.organization_name
        config.last_modified_by = user.id
        config.last_modified_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(config)
        return config

    def get_current_balance(self, delegacion: str) -> float:
        config = self.get_by_delegacion(delegacion)
        if not config:
            raise HTTPException(status_code=404, detail=f"Sin configuración para {delegacion}")
        opening = float(config.opening_balance)

        income = float(self.db.query(
            func.coalesce(func.sum(Transaction.amount), 0)
        ).filter(
            Transaction.delegacion == delegacion, Transaction.type == "income",
            Transaction.cancelled == False, Transaction.approval_status == "approved",
        ).scalar())

        expense = float(self.db.query(
            func.coalesce(func.sum(Transaction.amount), 0)
        ).filter(
            Transaction.delegacion == delegacion, Transaction.type == "expense",
            Transaction.cancelled == False, Transaction.approval_status == "approved",
        ).scalar())

        return opening + income - expense

    def _require_admin(self, u):
        if u.role != "admin":
            raise HTTPException(status_code=403, detail="Solo el Administrador puede gestionar la configuración")

    def _no_sessions(self, deleg):
        n = self.db.query(CashSession).filter(CashSession.delegacion == deleg).count()
        if n > 0:
            raise HTTPException(status_code=409, detail=f"No se puede modificar: {n} sesión(es) en {deleg}")
