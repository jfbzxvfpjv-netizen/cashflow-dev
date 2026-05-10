"""
M11 — Router de firmas de transacciones.
Gestiona la captura, listado, descarga y eliminacion de firmas Wacom STU
asociadas a transacciones. Una firma por transaccion y signer_type.
Respeta inmutabilidad de sesiones cerradas y transacciones canceladas.
"""
import hashlib
import base64
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.models.cash_flow import Transaction, TransactionSignature, CashSession
from app.models.audit_log import AuditLog

router = APIRouter(prefix="/transactions/{txn_id}/signatures", tags=["Firmas M11"])


class SignatureCreate(BaseModel):
    signer_type: str = Field(..., description="employee | supplier | partner | free_text")
    signer_name: str = Field(..., max_length=100)
    signature_data: str = Field(..., description="PNG en base64")
    status: Optional[str] = Field("valid", description="valid | provisional")
    employee_id: Optional[int] = None
    supplier_id: Optional[int] = None
    partner_id: Optional[int] = None
    device_model: Optional[str] = None
    width_px: Optional[int] = None
    height_px: Optional[int] = None
    duration_ms: Optional[int] = None
    fss_data_b64: Optional[str] = Field(None, description="FSS Wacom en base64")


class SignatureOut(BaseModel):
    id: int
    transaction_id: int
    signer_type: str
    signer_name: str
    status: Optional[str]
    employee_id: Optional[int]
    supplier_id: Optional[int]
    partner_id: Optional[int]
    device_model: Optional[str]
    signed_at: Optional[datetime]
    captured_by_user_id: Optional[int]


def _check_transaction_access(db: Session, txn_id: int, user: User) -> Transaction:
    txn = db.query(Transaction).filter(Transaction.id == txn_id).first()
    if not txn:
        raise HTTPException(status_code=404, detail="Transaccion no encontrada")
    if user.role == "gestor" and txn.delegacion != user.delegacion:
        raise HTTPException(status_code=403, detail="Sin acceso a esta delegacion")
    return txn


def _check_can_modify(db: Session, txn: Transaction):
    session = db.query(CashSession).filter(CashSession.id == txn.session_id).first()
    if session and session.status == "closed":
        raise HTTPException(status_code=400, detail="No se pueden modificar firmas de una sesion cerrada")
    if txn.cancelled:
        raise HTTPException(status_code=400, detail="No se pueden modificar firmas de una transaccion anulada")


@router.post("", status_code=201, response_model=SignatureOut)
async def create_signature(
    txn_id: int,
    body: SignatureCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    txn = _check_transaction_access(db, txn_id, user)
    _check_can_modify(db, txn)

    if body.signer_type not in ("employee", "supplier", "partner", "free_text"):
        raise HTTPException(status_code=400, detail="signer_type invalido")
    if body.status not in (None, "valid", "provisional"):
        raise HTTPException(status_code=400, detail="status invalido")

    existing = db.query(TransactionSignature).filter(
        TransactionSignature.transaction_id == txn_id,
        TransactionSignature.signer_type == body.signer_type
    ).first()
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Ya existe firma de tipo '{body.signer_type}' para esta transaccion"
        )

    try:
        png_bytes = base64.b64decode(body.signature_data)
    except Exception:
        raise HTTPException(status_code=400, detail="signature_data no es base64 valido")
    sha256 = hashlib.sha256(png_bytes).hexdigest()

    fss_bytes = None
    if body.fss_data_b64:
        try:
            fss_bytes = base64.b64decode(body.fss_data_b64)
        except Exception:
            raise HTTPException(status_code=400, detail="fss_data_b64 no es base64 valido")

    sig = TransactionSignature(
        transaction_id=txn_id,
        signer_type=body.signer_type,
        signer_name=body.signer_name,
        signature_data=body.signature_data,
        status=body.status or "valid",
        employee_id=body.employee_id,
        supplier_id=body.supplier_id,
        partner_id=body.partner_id,
        sha256_hash=sha256,
        device_model=body.device_model,
        width_px=body.width_px,
        height_px=body.height_px,
        duration_ms=body.duration_ms,
        fss_data=fss_bytes,
        captured_by_user_id=user.id,
    )
    db.add(sig)

    db.add(AuditLog(
        user_id=user.id,
        delegacion=txn.delegacion,
        action="CREATE_SIGNATURE",
        entity="TransactionSignature",
        entity_id=txn_id,
        details={"signer_type": body.signer_type, "signer_name": body.signer_name, "status": body.status}
    ))

    db.commit()
    db.refresh(sig)
    return sig


@router.get("", response_model=List[SignatureOut])
async def list_signatures(
    txn_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    _check_transaction_access(db, txn_id, user)
    sigs = db.query(TransactionSignature).filter(
        TransactionSignature.transaction_id == txn_id
    ).order_by(TransactionSignature.signed_at.asc()).all()
    return sigs


@router.get("/{sig_id}/image")
async def get_signature_image(
    txn_id: int,
    sig_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    _check_transaction_access(db, txn_id, user)
    sig = db.query(TransactionSignature).filter(
        TransactionSignature.id == sig_id,
        TransactionSignature.transaction_id == txn_id
    ).first()
    if not sig:
        raise HTTPException(status_code=404, detail="Firma no encontrada")
    try:
        png_bytes = base64.b64decode(sig.signature_data)
    except Exception:
        raise HTTPException(status_code=500, detail="Datos de firma corruptos")
    return Response(content=png_bytes, media_type="image/png")


@router.delete("/{sig_id}")
async def delete_signature(
    txn_id: int,
    sig_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    txn = _check_transaction_access(db, txn_id, user)
    _check_can_modify(db, txn)

    sig = db.query(TransactionSignature).filter(
        TransactionSignature.id == sig_id,
        TransactionSignature.transaction_id == txn_id
    ).first()
    if not sig:
        raise HTTPException(status_code=404, detail="Firma no encontrada")

    db.add(AuditLog(
        user_id=user.id,
        delegacion=txn.delegacion,
        action="DELETE_SIGNATURE",
        entity="TransactionSignature",
        entity_id=sig_id,
        details={"signer_type": sig.signer_type, "signer_name": sig.signer_name, "transaction_id": txn_id}
    ))
    db.delete(sig)
    db.commit()
    return {"detail": "Firma eliminada"}
