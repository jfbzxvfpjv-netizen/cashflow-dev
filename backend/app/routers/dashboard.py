"""
Router de Dashboard — M8
Endpoint GET /dashboard/summary con datos completos del panel principal.
"""
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user, get_delegacion_filter
from app.models.user import User
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/summary")
async def get_dashboard_summary(
    delegacion: Optional[str] = Query(None, description="Bata, Malabo o Consolidado"),
    date_start: Optional[date] = Query(None),
    date_end: Optional[date] = Query(None),
    tipo: Optional[str] = Query(None, description="income o expense"),
    category_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Devuelve todos los datos del dashboard: saldo, indicadores del día,
    alertas, movimientos paginados y datos de gráficos.
    """
    # Gestores de caja solo ven su delegación
    if current_user.role == 'gestor':
        delegacion = current_user.delegacion
    elif not delegacion:
        delegacion = None  # Admin/Contable sin filtro = todo

    return DashboardService.get_summary(
        db=db,
        delegacion=delegacion,
        date_start=date_start,
        date_end=date_end,
        tipo=tipo,
        category_id=category_id,
        page=page,
        page_size=page_size
    )
