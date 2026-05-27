"""
Módulo 6 — Router de umbrales de aprobación.
Gestiona la configuración de importes por encima de los cuales las transacciones
requieren aprobación del Administrador, y el listado de aprobaciones pendientes.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.deps import get_db, get_current_user, require_role
from app.models.user import User
from datetime import datetime
from pydantic import BaseModel, Field as PydField
from app.models.audit_log import AuditLog
from app.models.approvals import CategoryApprovalThreshold, ExpenseApproval
from app.models.catalogs import TransactionCategory
from app.models.cash_flow import Transaction
from app.schemas.approval import ThresholdCreate, ThresholdUpdate, ThresholdOut, ApprovalOut

router = APIRouter(prefix="/approvals", tags=["Aprobaciones"])


@router.get("/thresholds", response_model=List[ThresholdOut])
async def list_thresholds(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Lista umbrales de aprobacion configurados.
    Admin/contable ven todos. Gestor solo ve los de su delegacion."""
    thresholds = db.query(CategoryApprovalThreshold).all()
    result = []
    for t in thresholds:
        cat = db.query(TransactionCategory).filter(TransactionCategory.id == t.category_id).first()
        result.append(ThresholdOut(
            id=t.id, category_id=t.category_id,
            category_name=cat.name if cat else None,
            delegacion=t.delegacion,
            threshold_amount=t.threshold_amount,
            created_at=t.created_at
        ))
    return result


@router.post("/thresholds", response_model=ThresholdOut)
async def create_threshold(
    payload: ThresholdCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("admin"))
):
    """Crea un umbral de aprobación para una categoría y delegación."""
    existing = db.query(CategoryApprovalThreshold).filter(
        CategoryApprovalThreshold.category_id == payload.category_id,
        CategoryApprovalThreshold.delegacion == payload.delegacion
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Ya existe un umbral para esta categoría y delegación")

    t = CategoryApprovalThreshold(
        category_id=payload.category_id,
        delegacion=payload.delegacion,
        threshold_amount=payload.threshold_amount
    )
    db.add(t)
    db.commit()
    db.refresh(t)

    cat = db.query(TransactionCategory).filter(TransactionCategory.id == t.category_id).first()
    return ThresholdOut(
        id=t.id, category_id=t.category_id,
        category_name=cat.name if cat else None,
        delegacion=t.delegacion,
        threshold_amount=t.threshold_amount,
        created_at=t.created_at
    )


@router.put("/thresholds/{threshold_id}", response_model=ThresholdOut)
async def update_threshold(
    threshold_id: int,
    payload: ThresholdUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("admin"))
):
    """Modifica el importe de un umbral existente."""
    t = db.query(CategoryApprovalThreshold).filter(
        CategoryApprovalThreshold.id == threshold_id
    ).first()
    if not t:
        raise HTTPException(status_code=404, detail="Umbral no encontrado")
    t.threshold_amount = payload.threshold_amount
    db.commit()
    db.refresh(t)

    cat = db.query(TransactionCategory).filter(TransactionCategory.id == t.category_id).first()
    return ThresholdOut(
        id=t.id, category_id=t.category_id,
        category_name=cat.name if cat else None,
        delegacion=t.delegacion,
        threshold_amount=t.threshold_amount,
        created_at=t.created_at
    )


@router.delete("/thresholds/{threshold_id}")
async def delete_threshold(
    threshold_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("admin"))
):
    """Elimina un umbral de aprobación."""
    t = db.query(CategoryApprovalThreshold).filter(
        CategoryApprovalThreshold.id == threshold_id
    ).first()
    if not t:
        raise HTTPException(status_code=404, detail="Umbral no encontrado")
    db.delete(t)
    db.commit()
    return {"detail": "Umbral eliminado"}


@router.get("/pending", response_model=List[ApprovalOut])
async def list_pending_approvals(
    db: Session = Depends(get_db),
    user: User = Depends(require_role("admin"))
):
    """Lista todas las aprobaciones pendientes con datos de la transacción."""
    approvals = db.query(ExpenseApproval).filter(
        ExpenseApproval.status == "pending"
    ).order_by(ExpenseApproval.requested_at.desc()).all()
    result = []
    for a in approvals:
        txn = db.query(Transaction).filter(Transaction.id == a.transaction_id).first()
        result.append(ApprovalOut(
            id=a.id, transaction_id=a.transaction_id,
            reference_number=txn.reference_number if txn else None,
            concept=txn.concept if txn else None,
            amount=txn.amount if txn else None,
            requested_by=a.requested_by,
            requested_at=a.requested_at,
            approved_by=a.approved_by,
            approved_at=a.approved_at,
            status=a.status,
            rejection_reason=a.rejection_reason
        ))
    return result


# ── Endpoints de acción sobre aprobaciones pendientes (M10a) ────────────────

class _RejectPayload(BaseModel):
    rejection_reason: str = PydField(..., min_length=5, max_length=500)


@router.put("/pending/{approval_id}/approve", response_model=ApprovalOut)
async def approve_pending(
    approval_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("admin")),
):
    """Admin aprueba una solicitud pendiente.
    Marca ExpenseApproval y Transaction como 'approved'.
    Tras esto la transacción cuenta en saldos (los filtros approval_status='approved' lo recogen).
    """
    a = db.query(ExpenseApproval).filter(ExpenseApproval.id == approval_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="Aprobación no encontrada")
    if a.status != "pending":
        raise HTTPException(status_code=400, detail=f"No se puede aprobar: estado actual '{a.status}'")

    now = datetime.utcnow()
    a.status = "approved"
    a.approved_by = user.id
    a.approved_at = now

    txn = db.query(Transaction).filter(Transaction.id == a.transaction_id).first()
    if txn:
        txn.approval_status = "approved"
        txn.approved_by = user.id
        txn.approved_at = now

    db.add(AuditLog(
        user_id=user.id, delegacion=txn.delegacion if txn else None,
        action="APPROVAL_APPROVED", entity="expense_approval",
        entity_id=a.id, details={"transaction_id": a.transaction_id},
    ))
    db.commit()
    db.refresh(a)

    return ApprovalOut(
        id=a.id, transaction_id=a.transaction_id,
        reference_number=txn.reference_number if txn else None,
        concept=txn.concept if txn else None,
        amount=txn.amount if txn else None,
        requested_by=a.requested_by, requested_at=a.requested_at,
        approved_by=a.approved_by, approved_at=a.approved_at,
        status=a.status, rejection_reason=a.rejection_reason,
    )


@router.put("/pending/{approval_id}/reject", response_model=ApprovalOut)
async def reject_pending(
    approval_id: int,
    payload: _RejectPayload,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("admin")),
):
    """Admin rechaza una solicitud pendiente con motivo obligatorio.
    Marca ExpenseApproval y Transaction como 'rejected'.
    La transacción queda registrada pero NO cuenta en saldos.
    """
    a = db.query(ExpenseApproval).filter(ExpenseApproval.id == approval_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="Aprobación no encontrada")
    if a.status != "pending":
        raise HTTPException(status_code=400, detail=f"No se puede rechazar: estado actual '{a.status}'")

    now = datetime.utcnow()
    a.status = "rejected"
    a.approved_by = user.id
    a.approved_at = now
    a.rejection_reason = payload.rejection_reason

    txn = db.query(Transaction).filter(Transaction.id == a.transaction_id).first()
    if txn:
        txn.approval_status = "rejected"

    db.add(AuditLog(
        user_id=user.id, delegacion=txn.delegacion if txn else None,
        action="APPROVAL_REJECTED", entity="expense_approval",
        entity_id=a.id, details={"transaction_id": a.transaction_id, "reason": payload.rejection_reason},
    ))
    db.commit()
    db.refresh(a)

    return ApprovalOut(
        id=a.id, transaction_id=a.transaction_id,
        reference_number=txn.reference_number if txn else None,
        concept=txn.concept if txn else None,
        amount=txn.amount if txn else None,
        requested_by=a.requested_by, requested_at=a.requested_at,
        approved_by=a.approved_by, approved_at=a.approved_at,
        status=a.status, rejection_reason=a.rejection_reason,
    )
