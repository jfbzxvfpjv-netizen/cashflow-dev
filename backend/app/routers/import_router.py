"""
Router de importación desde Excel.
Endpoints para validar, ejecutar e historial de importaciones.
Solo accesible por el Administrador.
"""
from fastapi import APIRouter, Depends, UploadFile, File, Query, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user, require_role
from app.models.user import User
from app.services.import_service import ImportService
from app.schemas.import_schema import ValidationSummary, ImportResult, ImportHistoryOut

router = APIRouter(prefix="/import", tags=["Importación Excel"])


@router.post("/validate", response_model=ValidationSummary)
async def validate_excel(
    file: UploadFile = File(...),
    delegacion: str = Query(..., regex="^(Bata|Malabo)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    """Valida un fichero Excel sin importar. Devuelve informe completo."""
    if not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="El fichero debe ser .xlsx o .xls")

    file_bytes = await file.read()
    if len(file_bytes) == 0:
        raise HTTPException(status_code=400, detail="El fichero está vacío")

    result = ImportService.validate_excel(db, file_bytes, delegacion)
    return result


@router.post("/execute", response_model=ImportResult)
async def execute_import(
    file: UploadFile = File(...),
    delegacion: str = Query(..., regex="^(Bata|Malabo)$"),
    confirmed: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    """Ejecuta la importación tras validación exitosa."""
    if not confirmed:
        raise HTTPException(status_code=400, detail="Debe confirmar la importación con confirmed=true")

    if not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="El fichero debe ser .xlsx o .xls")

    file_bytes = await file.read()
    if len(file_bytes) == 0:
        raise HTTPException(status_code=400, detail="El fichero está vacío")

    try:
        result = ImportService.execute_import(
            db, file_bytes, delegacion, current_user.id, file.filename
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/history", response_model=list[ImportHistoryOut])
async def get_import_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    """Lista el historial de importaciones realizadas."""
    return ImportService.get_history(db)
