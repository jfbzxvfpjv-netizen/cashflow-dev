"""
Router de Informes — M8
Endpoints de informe de cierre de sesión y de período libre.
Exportables en PDF y Excel.
"""
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user, require_role
from app.models.user import User
from app.models.cash_flow import CashSession
from app.services.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["Informes"])


@router.get("/session/{session_id}")
async def report_session(
    session_id: int,
    format: str = Query("pdf", description="pdf o xlsx"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Informe de cierre de sesión. Accesible por admin, contable y gestor.
    El gestor solo puede ver sesiones de su delegación.
    """
    # Verificar acceso
    session = db.query(CashSession).filter(CashSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")

    if current_user.role == 'gestor' and session.delegacion != current_user.delegacion:
        raise HTTPException(status_code=403, detail="Sin acceso a sesiones de otra delegación")

    if current_user.role == 'consulta':
        pass  # Consulta puede ver informes

    if format == 'xlsx':
        content = ReportService.generate_session_xlsx(db, session_id)
        if not content:
            raise HTTPException(status_code=404, detail="No se pudo generar el informe")
        return Response(
            content=content,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename=cierre_sesion_{session_id}.xlsx"
            }
        )
    else:
        content = ReportService.generate_session_pdf(db, session_id)
        if not content:
            raise HTTPException(status_code=404, detail="No se pudo generar el informe")
        # Detectar si es PDF real o HTML fallback
        if content[:5] == b'%PDF-':
            media = "application/pdf"
            ext = "pdf"
        else:
            media = "text/html"
            ext = "html"
        return Response(
            content=content,
            media_type=media,
            headers={
                "Content-Disposition": f"attachment; filename=cierre_sesion_{session_id}.{ext}"
            }
        )


@router.get("/period")
async def report_period(
    date_start: date = Query(..., description="Fecha inicio"),
    date_end: date = Query(..., description="Fecha fin"),
    delegacion: Optional[str] = Query(None),
    category_id: Optional[int] = Query(None),
    project_id: Optional[int] = Query(None),
    format: str = Query("pdf", description="pdf o xlsx"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Informe de período libre con filtros. Accesible por admin, contable y consulta.
    """
    # Gestores de caja: solo su delegación
    if current_user.role == 'gestor':
        delegacion = current_user.delegacion

    if format == 'xlsx':
        content = ReportService.generate_period_xlsx(
            db, delegacion, date_start, date_end, category_id, project_id
        )
        return Response(
            content=content,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename=informe_periodo_{date_start}_{date_end}.xlsx"
            }
        )
    else:
        content = ReportService.generate_period_pdf(
            db, delegacion, date_start, date_end, category_id, project_id
        )
        if content[:5] == b'%PDF-':
            media = "application/pdf"
            ext = "pdf"
        else:
            media = "text/html"
            ext = "html"
        return Response(
            content=content,
            media_type=media,
            headers={
                "Content-Disposition": f"attachment; filename=informe_periodo_{date_start}_{date_end}.{ext}"
            }
        )
