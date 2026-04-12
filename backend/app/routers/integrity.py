"""
Módulo 6 — Router de verificación de integridad SHA-256.
Permite al Administrador verificar que ninguna transacción ha sido manipulada
directamente en la base de datos eludiendo la aplicación.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_role
from app.models.user import User
from app.services.transaction_service import TransactionService

router = APIRouter(prefix="/integrity", tags=["Integridad"])


@router.get("/verify")
async def verify_all(
    db: Session = Depends(get_db),
    user: User = Depends(require_role("admin"))
):
    """Verifica el hash SHA-256 de todas las transacciones del sistema."""
    return TransactionService.verify_all_integrity(db)


@router.get("/verify/{txn_id}")
async def verify_single(
    txn_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("admin"))
):
    """Verifica el hash SHA-256 de una transacción individual."""
    try:
        return TransactionService.verify_single_integrity(db, txn_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
