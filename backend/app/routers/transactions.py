"""
Módulo 6 — Router de transacciones.
Endpoints para crear, editar, cancelar, listar, aprobar/rechazar transacciones
y verificar integridad SHA-256.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, date

from app.core.deps import get_db, get_current_user, require_role
from app.models.user import User
from app.models.cash_flow import (
    Transaction, TransactionProject, TransactionAttachment, TransactionSignature
)
from app.models.catalogs import (
    TransactionCategory, TransactionSubcategory, Project, Work
)
from app.schemas.transaction import (
    TransactionCreate, TransactionUpdate, TransactionOut,
    TransactionDetail, TransactionListResponse,
    TransactionProjectOut, CancelRequest, RejectRequest
)
from app.services.transaction_service import TransactionService

router = APIRouter(prefix="/transactions", tags=["Transacciones"])


def _enrich_transaction(db: Session, txn: Transaction) -> dict:
    """Enriquece una transacción con datos de relaciones para la respuesta."""
    now = datetime.utcnow()

    # Categoría y subcategoría
    cat = db.query(TransactionCategory).filter(TransactionCategory.id == txn.category_id).first()
    subcat = db.query(TransactionSubcategory).filter(TransactionSubcategory.id == txn.subcategory_id).first()

    # Usuario
    user = db.query(User).filter(User.id == txn.user_id).first()

    # Proyectos
    tps = db.query(TransactionProject).filter(TransactionProject.transaction_id == txn.id).all()
    projects_out = []
    for tp in tps:
        proj = db.query(Project).filter(Project.id == tp.project_id).first()
        work = db.query(Work).filter(Work.id == tp.work_id).first()
        projects_out.append(TransactionProjectOut(
            project_id=tp.project_id,
            work_id=tp.work_id,
            project_name=proj.name if proj else None,
            work_name=work.name if work else None
        ))

    # Adjuntos y firmas
    att_count = db.query(TransactionAttachment).filter(
        TransactionAttachment.transaction_id == txn.id
    ).count()
    sig_count = db.query(TransactionSignature).filter(
        TransactionSignature.transaction_id == txn.id
    ).count()

    # Estado de edición
    if txn.imported and txn.imported_editable_until:
        is_editable = now <= txn.imported_editable_until and not txn.cancelled
        remaining = max(0, int((txn.imported_editable_until - now).total_seconds())) if is_editable else 0
    else:
        is_editable = now <= txn.editable_until and not txn.cancelled
        remaining = max(0, int((txn.editable_until - now).total_seconds())) if is_editable else 0

    # Comprobar sesión cerrada
    # Excepción: importados dentro de ventana de 30 días pueden editarse
    from app.models.cash_flow import CashSession
    sess = db.query(CashSession).filter(CashSession.id == txn.session_id).first()
    if sess and sess.status == "closed":
        if not (txn.imported and txn.imported_editable_until and now <= txn.imported_editable_until):
            is_editable = False
            remaining = 0

        # -- counterparty_name (Fix 1) --
    counterparty_name = None
    if txn.supplier_id:
        from app.models.catalogs import Supplier
        sup = db.query(Supplier).filter(Supplier.id == txn.supplier_id).first()
        if sup:
            counterparty_name = sup.name
    if counterparty_name is None and txn.employee_id:
        from app.models.catalogs import Employee
        emp = db.query(Employee).filter(Employee.id == txn.employee_id).first()
        if emp:
            counterparty_name = emp.full_name
    if counterparty_name is None and txn.partner_id:
        from app.models.catalogs import Partner
        par = db.query(Partner).filter(Partner.id == txn.partner_id).first()
        if par:
            counterparty_name = par.full_name
    if counterparty_name is None and txn.counterparty_free:
        counterparty_name = txn.counterparty_free

    return {
        "category_name": cat.name if cat else None,
        "subcategory_name": subcat.name if subcat else None,
        "user_fullname": user.full_name if user else None,
        "projects": projects_out,
        "has_attachments": att_count > 0,
        "has_signatures": sig_count > 0,
        "is_editable": is_editable,
        "counterparty_name": counterparty_name,
        "seconds_remaining": remaining
    }


@router.post("", response_model=TransactionOut)
async def create_transaction(
    payload: TransactionCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("gestor", "admin"))
):
    """Crea una transacción nueva en la sesión activa del usuario."""
    try:
        txn = TransactionService.create_transaction(db, payload.model_dump(), user)
        enriched = _enrich_transaction(db, txn)
        return TransactionOut.model_validate({**txn.__dict__, **enriched})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{txn_id}", response_model=TransactionOut)
async def update_transaction(
    txn_id: int,
    payload: TransactionUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("admin"))
):
    """Modifica una transacción dentro de su ventana de edición."""
    try:
        txn = TransactionService.update_transaction(
            db, txn_id, payload.model_dump(exclude_unset=True), user
        )
        enriched = _enrich_transaction(db, txn)
        return TransactionOut.model_validate({**txn.__dict__, **enriched})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.delete("/{txn_id}", response_model=TransactionOut)
async def cancel_transaction(
    txn_id: int,
    payload: CancelRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("admin"))
):
    """Cancela una transacción generando una contrapartida inversa."""
    try:
        txn = TransactionService.cancel_transaction(db, txn_id, payload.reason, user)
        enriched = _enrich_transaction(db, txn)
        return TransactionOut.model_validate({**txn.__dict__, **enriched})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=TransactionListResponse)
async def list_transactions(
    delegacion: Optional[str] = None,
    session_id: Optional[int] = None,
    type: Optional[str] = None,
    category_id: Optional[int] = None,
    subcategory_id: Optional[int] = None,
    project_id: Optional[int] = None,
    work_id: Optional[int] = None,
    supplier_id: Optional[int] = None,
    employee_id: Optional[int] = None,
    partner_id: Optional[int] = None,
    vehicle_id: Optional[int] = None,
    transaction_type: Optional[str] = None,
    approval_status: Optional[str] = None,
    imported: Optional[bool] = None,
    cancelled: Optional[bool] = None,
    date_start: Optional[str] = None,
    date_end: Optional[str] = None,
    concept: Optional[str] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Lista transacciones con filtros avanzados y paginación."""
    filters = {
        "delegacion": delegacion, "session_id": session_id, "type": type,
        "category_id": category_id, "subcategory_id": subcategory_id,
        "project_id": project_id, "work_id": work_id,
        "supplier_id": supplier_id, "employee_id": employee_id,
        "partner_id": partner_id, "vehicle_id": vehicle_id,
        "transaction_type": transaction_type, "approval_status": approval_status,
        "imported": imported, "cancelled": cancelled,
        "concept": concept, "min_amount": min_amount, "max_amount": max_amount,
        "page": page, "page_size": page_size
    }
    if date_start:
        filters["date_start"] = datetime.fromisoformat(date_start)
    if date_end:
        filters["date_end"] = datetime.fromisoformat(date_end)

    result = TransactionService.list_transactions(db, filters, user)

    items_out = []
    for txn in result["items"]:
        enriched = _enrich_transaction(db, txn)
        items_out.append(TransactionOut.model_validate({**txn.__dict__, **enriched}))

    return TransactionListResponse(
        items=items_out,
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"],
        pages=result["pages"]
    )


@router.get("/{txn_id}", response_model=TransactionDetail)
async def get_transaction(
    txn_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Detalle completo de una transacción con estado de edición."""
    txn = TransactionService.get_transaction_detail(db, txn_id, user)
    if not txn:
        raise HTTPException(status_code=404, detail="Transacción no encontrada")
    enriched = _enrich_transaction(db, txn)
    return TransactionDetail.model_validate({**txn.__dict__, **enriched})


@router.put("/{txn_id}/approve", response_model=TransactionOut)
async def approve_transaction(
    txn_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("admin"))
):
    """Aprueba una transacción pendiente de aprobación."""
    try:
        txn = TransactionService.approve_transaction(db, txn_id, user)
        enriched = _enrich_transaction(db, txn)
        return TransactionOut.model_validate({**txn.__dict__, **enriched})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{txn_id}/reject", response_model=TransactionOut)
async def reject_transaction(
    txn_id: int,
    payload: RejectRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("admin"))
):
    """Rechaza una transacción pendiente con motivo obligatorio."""
    try:
        txn = TransactionService.reject_transaction(db, txn_id, payload.reason, user)
        enriched = _enrich_transaction(db, txn)
        return TransactionOut.model_validate({**txn.__dict__, **enriched})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{txn_id}/execute", response_model=TransactionOut)
async def execute_transaction(
    txn_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("gestor", "admin"))
):
    """El Gestor confirma la ejecución física del pago autorizado."""
    try:
        txn = TransactionService.execute_transaction(db, txn_id, user)
        enriched = _enrich_transaction(db, txn)
        return TransactionOut.model_validate({**txn.__dict__, **enriched})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
