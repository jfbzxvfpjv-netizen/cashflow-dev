"""
Router de desarrollo (reset y fixtures) y endpoint de información del sistema.
Los endpoints /dev/* solo existen cuando ENV=development.
En producción devuelven HTTP 404 sin ningún mensaje revelador.
El endpoint /system/env es público y se usa para el banner de desarrollo.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user, require_role
from app.config import settings
from app.models.user import User
from app.schemas.dev_schema import ConfirmAction, DevResult, EnvInfo
from app.services.dev_service import DevService

router = APIRouter(tags=["Desarrollo"])


# --- Endpoint público de información del sistema ---
@router.get("/system/env", response_model=EnvInfo)
async def get_system_env():
    """Devuelve el entorno actual. Usado por App.vue para el banner de desarrollo."""
    return {"env": settings.ENV}


# --- Endpoints de desarrollo (solo ENV=development) ---
def _check_dev_env():
    """Verificación centralizada del entorno. 404 en producción."""
    if settings.ENV != "development":
        raise HTTPException(status_code=404)


@router.post("/dev/reset-data", response_model=DevResult)
async def reset_data(
    body: ConfirmAction,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    """Borra transacciones conservando catálogos. Solo en ENV=development."""
    _check_dev_env()
    if body.confirm != "RESET":
        raise HTTPException(status_code=400, detail="Debe escribir 'RESET' para confirmar")
    return DevService.reset_data(db)


@router.post("/dev/reset-full", response_model=DevResult)
async def reset_full(
    body: ConfirmAction,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    """Borra TODO y re-ejecuta seed.py. Solo en ENV=development."""
    _check_dev_env()
    if body.confirm != "RESET":
        raise HTTPException(status_code=400, detail="Debe escribir 'RESET' para confirmar")
    return DevService.reset_full(db)


@router.post("/dev/load-fixture/{nombre}", response_model=DevResult)
async def load_fixture(
    nombre: str,
    body: ConfirmAction,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    """Carga fixture predefinido. Solo en ENV=development."""
    _check_dev_env()
    if body.confirm != "LOAD":
        raise HTTPException(status_code=400, detail="Debe escribir 'LOAD' para confirmar")
    try:
        return DevService.load_fixture(db, nombre, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
