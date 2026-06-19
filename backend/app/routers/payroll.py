"""
Router M10b — Nóminas.
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.services.payroll_service import PayrollService
from app.schemas.payroll import (
    PayrollPeriodCreate, PayrollPeriodRead, PayrollPeriodDetail,
    PayrollEntryUpdate, PayrollEntryRead,
    PayrollExecutePayload, PayrollExecuteResult,
    PayrollPayPayload, PayrollPayResult,
)

router = APIRouter(prefix="/payrolls", tags=["payrolls"])


@router.post("", response_model=PayrollPeriodRead)
def generate(data: PayrollPeriodCreate, db: Session = Depends(get_db),
             user: User = Depends(get_current_user)):
    """Admin genera un periodo de nómina con N entries (snapshot)."""
    svc = PayrollService(db)
    period = svc.generate_period(data, user)
    return svc._enrich_period(period)


@router.get("", response_model=List[PayrollPeriodRead])
def list_all(year: Optional[int] = None, delegacion: Optional[str] = None,
             status: Optional[str] = None, db: Session = Depends(get_db),
             user: User = Depends(get_current_user)):
    """Lista periodos (gestor filtrado a su delegación)."""
    svc = PayrollService(db)
    return svc.list_periods(year=year, delegacion=delegacion, status=status, user=user)


@router.get("/{period_id}", response_model=PayrollPeriodDetail)
def detail(period_id: int, db: Session = Depends(get_db),
           user: User = Depends(get_current_user)):
    """Detalle del periodo con todas las entries."""
    svc = PayrollService(db)
    return svc.get_period_detail(period_id, user)


@router.put("/{period_id}/entries/{entry_id}", response_model=PayrollEntryRead)
def update_entry(period_id: int, entry_id: int, data: PayrollEntryUpdate,
                 db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Admin edita cash_amount o notes de una entry (solo si periodo en draft)."""
    svc = PayrollService(db)
    entry = svc.update_entry(entry_id, data, user)
    return svc._enrich_entry(entry)


@router.post("/{period_id}/execute", response_model=PayrollExecuteResult)
def execute(period_id: int, payload: PayrollExecutePayload,
            db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Gestor (o admin) lanza pagos: crea Transactions para entries pendientes."""
    svc = PayrollService(db)
    return svc.execute_entries(period_id, payload, user)


@router.put("/{period_id}/close", response_model=PayrollPeriodRead)
def close(period_id: int, db: Session = Depends(get_db),
          user: User = Depends(get_current_user)):
    """Admin cierra el periodo (status='paid')."""
    svc = PayrollService(db)
    period = svc.close_period(period_id, user)
    return svc._enrich_period(period)


@router.post("/{period_id}/entries/{entry_id}/pay", response_model=PayrollPayResult)
def pay_entry(period_id: int, entry_id: int, payload: PayrollPayPayload,
              db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Gestor paga una entrada individual de nómina con firma del empleado."""
    svc = PayrollService(db)
    return svc.pay_entry(period_id, entry_id, payload.signature, user)

@router.put("/{period_id}/entries/{entry_id}/liquidate-no-cash")
async def liquidate_no_cash(
    period_id: int,
    entry_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """M10b-v3: liquida deducciones SIN movimiento de caja (deudor neto cronico).
    Solo gestor de la delegacion, entry con cash_amount=0 y deducciones>0.
    """
    svc = PayrollService(db)
    return svc.liquidate_without_cash(period_id, entry_id, user)
@router.delete("/{period_id}")
def delete_period(period_id: int, db: Session = Depends(get_db),
                  user: User = Depends(get_current_user)):
    """Borra un periodo de nomina (desarrollo: ENV=development, ventana 30 min,
    admin/contable). Revierte deducciones y elimina transacciones de sesiones abiertas."""
    svc = PayrollService(db)
    return svc.delete_period(period_id, user)
