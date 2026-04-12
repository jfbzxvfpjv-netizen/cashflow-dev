"""
Parche M6 — Router de adjuntos de transacciones.
Gestiona la subida, listado, descarga y eliminación de ficheros adjuntos
vinculados a transacciones. Respeta la política de inmutabilidad: no se
pueden añadir ni eliminar adjuntos en sesiones cerradas ni fuera de la
ventana de edición.
"""
import os
import uuid
import shutil
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List

from app.core.deps import get_db, get_current_user, require_role
from app.config import settings
from app.models.user import User
from app.models.cash_flow import Transaction, TransactionAttachment, CashSession
from app.models.audit_log import AuditLog

router = APIRouter(prefix="/transactions/{txn_id}/attachments", tags=["Adjuntos"])

UPLOAD_DIR = "/app/uploads"


def _check_transaction_access(db: Session, txn_id: int, user: User) -> Transaction:
    """Verifica que la transacción existe y el usuario tiene acceso."""
    txn = db.query(Transaction).filter(Transaction.id == txn_id).first()
    if not txn:
        raise HTTPException(status_code=404, detail="Transacción no encontrada")
    if user.role == "gestor" and txn.delegacion != user.delegacion:
        raise HTTPException(status_code=403, detail="Sin acceso a esta delegación")
    return txn


def _check_can_modify(db: Session, txn: Transaction):
    """Verifica que se pueden añadir/eliminar adjuntos en esta transacción."""
    # Sesión cerrada: no se permiten modificaciones
    session = db.query(CashSession).filter(CashSession.id == txn.session_id).first()
    if session and session.status == "closed":
        raise HTTPException(status_code=400, detail="No se pueden modificar adjuntos de una sesión cerrada")
    if txn.cancelled:
        raise HTTPException(status_code=400, detail="No se pueden modificar adjuntos de una transacción anulada")


@router.post("", status_code=201)
async def upload_attachment(
    txn_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Sube un fichero adjunto a una transacción. Valida límites de tamaño
    por fichero y por transacción. Cualquier formato aceptado.
    """
    txn = _check_transaction_access(db, txn_id, user)
    _check_can_modify(db, txn)

    # Leer contenido para verificar tamaño
    content = await file.read()
    file_size = len(content)

    # Límite por fichero
    max_file_bytes = (getattr(settings, "MAX_FILE_SIZE_MB", 10)) * 1024 * 1024
    if file_size > max_file_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"El fichero supera el límite de {getattr(settings, 'MAX_FILE_SIZE_MB', 10)} MB"
        )

    # Límite total por transacción
    max_txn_bytes = (getattr(settings, "MAX_TRANSACTION_FILES_MB", 50)) * 1024 * 1024
    existing_size = db.query(
        TransactionAttachment.file_size_bytes
    ).filter(TransactionAttachment.transaction_id == txn_id).all()
    total_existing = sum(s[0] for s in existing_size if s[0])
    if total_existing + file_size > max_txn_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"Se superaría el límite total de {getattr(settings, 'MAX_TRANSACTION_FILES_MB', 50)} MB por transacción"
        )

    # Guardar fichero en disco
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    ext = os.path.splitext(file.filename)[1] if file.filename else ""
    stored_name = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(UPLOAD_DIR, stored_name)

    with open(file_path, "wb") as f:
        f.write(content)

    # Registrar en BD
    attachment = TransactionAttachment(
        transaction_id=txn_id,
        original_filename=file.filename or "sin_nombre",
        stored_filename=stored_name,
        mime_type=file.content_type or "application/octet-stream",
        file_size_bytes=file_size,
        file_path=file_path,
        uploaded_by=user.id,
        locked=False
    )
    db.add(attachment)

    # Auditoría
    db.add(AuditLog(
        user_id=user.id,
        delegacion=txn.delegacion,
        action="UPLOAD_ATTACHMENT",
        entity="TransactionAttachment",
        entity_id=txn_id,
        details={"filename": file.filename, "size_bytes": file_size}
    ))

    db.commit()
    db.refresh(attachment)

    return {
        "id": attachment.id,
        "transaction_id": attachment.transaction_id,
        "original_filename": attachment.original_filename,
        "mime_type": attachment.mime_type,
        "file_size_bytes": attachment.file_size_bytes,
        "uploaded_at": str(attachment.uploaded_at),
        "locked": attachment.locked
    }


@router.get("")
async def list_attachments(
    txn_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Lista los metadatos de todos los adjuntos de una transacción."""
    txn = _check_transaction_access(db, txn_id, user)
    attachments = db.query(TransactionAttachment).filter(
        TransactionAttachment.transaction_id == txn_id
    ).order_by(TransactionAttachment.uploaded_at.desc()).all()

    return [
        {
            "id": a.id,
            "transaction_id": a.transaction_id,
            "original_filename": a.original_filename,
            "mime_type": a.mime_type,
            "file_size_bytes": a.file_size_bytes,
            "uploaded_at": str(a.uploaded_at),
            "locked": a.locked
        }
        for a in attachments
    ]


@router.get("/{att_id}")
async def download_attachment(
    txn_id: int,
    att_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Descarga un fichero adjunto por su ID."""
    _check_transaction_access(db, txn_id, user)
    attachment = db.query(TransactionAttachment).filter(
        TransactionAttachment.id == att_id,
        TransactionAttachment.transaction_id == txn_id
    ).first()
    if not attachment:
        raise HTTPException(status_code=404, detail="Adjunto no encontrado")

    if not os.path.exists(attachment.file_path):
        raise HTTPException(status_code=404, detail="Fichero no encontrado en disco")

    return FileResponse(
        path=attachment.file_path,
        filename=attachment.original_filename,
        media_type=attachment.mime_type
    )


@router.delete("/{att_id}")
async def delete_attachment(
    txn_id: int,
    att_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Elimina un adjunto si no está bloqueado y la transacción permite
    modificaciones (sesión abierta, no cancelada).
    """
    txn = _check_transaction_access(db, txn_id, user)
    _check_can_modify(db, txn)

    attachment = db.query(TransactionAttachment).filter(
        TransactionAttachment.id == att_id,
        TransactionAttachment.transaction_id == txn_id
    ).first()
    if not attachment:
        raise HTTPException(status_code=404, detail="Adjunto no encontrado")

    if attachment.locked:
        raise HTTPException(status_code=403, detail="El adjunto está bloqueado y no se puede eliminar")

    # Eliminar fichero de disco
    if os.path.exists(attachment.file_path):
        os.remove(attachment.file_path)

    # Auditoría
    db.add(AuditLog(
        user_id=user.id,
        delegacion=txn.delegacion,
        action="DELETE_ATTACHMENT",
        entity="TransactionAttachment",
        entity_id=att_id,
        details={"filename": attachment.original_filename, "transaction_id": txn_id}
    ))

    db.delete(attachment)
    db.commit()

    return {"detail": "Adjunto eliminado"}
