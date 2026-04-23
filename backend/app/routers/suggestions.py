"""Router de sugerencias de categorización.

Endpoint único en v1: GET /suggestions/transaction-categorization.
Diseñado para alimentar el autocompletado del formulario de transacción.

Consulta pura de lectura; no modifica estado. Filtrado por delegación
respeta reglas del gestor (solo su delegación) pero admin y contable
pueden consultar global pasando el parámetro explícitamente.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user, require_role
from app.schemas.suggestions import CategorizationSuggestionOut
from app.services import suggestion_service

router = APIRouter(prefix="/suggestions", tags=["suggestions"])


@router.get(
    "/transaction-categorization",
    response_model=CategorizationSuggestionOut,
    summary="Sugerir categoría/subcategoría según histórico",
    description=(
        "Devuelve una sugerencia de category_id/subcategory_id basada en "
        "el concepto y la contraparte introducidos por el gestor, combinados "
        "con el histórico de transacciones aprobadas. Al menos uno de "
        "`concept` o algún campo de contraparte debe venir no vacío."
    ),
)
async def suggest_categorization(
    concept: Optional[str] = Query(None, max_length=500),
    supplier_id: Optional[int] = Query(None, ge=1),
    employee_id: Optional[int] = Query(None, ge=1),
    partner_id: Optional[int] = Query(None, ge=1),
    counterparty_free: Optional[str] = Query(None, max_length=150),
    project_id: Optional[int] = Query(None, ge=1),
    delegacion: Optional[str] = Query(None, pattern=r"^(Bata|Malabo)$"),
    db: Session = Depends(get_db),
    user = Depends(require_role("gestor", "admin", "contable")),
) -> CategorizationSuggestionOut:
    # Validación mínima: al menos un campo útil
    has_concept = bool(concept and concept.strip())
    has_counterparty = any([
        supplier_id, employee_id, partner_id,
        counterparty_free and counterparty_free.strip(),
    ])
    if not has_concept and not has_counterparty:
        raise HTTPException(
            status_code=400,
            detail="Se requiere al menos concept o una contraparte (supplier_id, employee_id, partner_id o counterparty_free).",
        )

    # Resolución de delegación efectiva:
    # - gestor: siempre su propia delegación (ignora param si se pasa otra distinta)
    # - admin/contable: usan el param si viene; si no, no filtran (None)
    if user.role == "gestor":
        effective_delegacion = user.delegacion
    else:
        effective_delegacion = delegacion

    result = suggestion_service.suggest_categorization(
        db=db,
        concept=concept,
        supplier_id=supplier_id,
        employee_id=employee_id,
        partner_id=partner_id,
        counterparty_free=counterparty_free,
        project_id=project_id,
        delegacion=effective_delegacion,
    )

    return CategorizationSuggestionOut(**result)
