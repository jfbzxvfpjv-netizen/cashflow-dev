"""
M11 Fingerprint - Endpoints REST.
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.v1.auth import get_current_user
from app.models.user import User
from app.models.cash_flow import EmployeeFingerprint
from app.models.catalogs import Employee
from app.schemas.fingerprints import (
    QualityRequest, QualityResponse,
    EnrollRequest, EnrollResponse,
    VerifyRequest, VerifyResponse,
    EmployeeFingerprintsResponse, FingerprintMetadata,
    EmployeeWithEnrollment,
    EnginStatusResponse,
    SignatureMethodResponse,
)
from app.services import fingerprint_service
from app.services.fingerprint_engine import get_engine, FingerprintEngineError


router = APIRouter(prefix="/fingerprints", tags=["M11 Fingerprint"])


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Restringe a usuarios con role=admin."""
    if current_user.role != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Requiere rol admin")
    return current_user


def require_admin_or_gestor(current_user: User = Depends(get_current_user)) -> User:
    """Permite admin y gestor. Para el gestor, el filtrado/validacion por
    delegacion se aplica en cada handler que expone empleados."""
    if current_user.role not in ("admin", "gestor"):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Requiere rol admin o gestor")
    return current_user


# ── Calidad / pre-check ─────────────────────────────────────────────────────

@router.post("/quality", response_model=QualityResponse)
def post_quality(
    payload: QualityRequest,
    current_user: User = Depends(require_admin_or_gestor),
):
    """Evalua calidad de una imagen sin persistir nada. Util durante enrolment."""
    try:
        return fingerprint_service.assess_quality(payload.image_b64)
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))
    except FingerprintEngineError as e:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"Motor: {e}")


# ── Enrolment ───────────────────────────────────────────────────────────────

@router.post("/enroll", response_model=EnrollResponse)
def post_enroll(
    payload: EnrollRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_gestor),
):
    """Enrola las 4 capturas de un dedo de un empleado. Atomico: o todas o ninguna.
    Falla con 409 si el dedo ya esta enrolado (eliminar primero)."""
    if current_user.role == "gestor":
        emp = db.query(Employee).filter(Employee.id == payload.employee_id).first()
        if not emp:
            raise HTTPException(status.HTTP_404_NOT_FOUND, f"Employee {payload.employee_id} no existe")
        if emp.delegacion not in (current_user.delegacion, "Ambas"):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "El empleado no pertenece a tu delegacion")
    try:
        return fingerprint_service.enroll_employee_finger(
            db=db,
            employee_id=payload.employee_id,
            finger_position=payload.finger_position,
            images_b64=payload.images_b64,
            current_user=current_user,
        )
    except ValueError as e:
        msg = str(e)
        if "ya esta enrolado" in msg:
            raise HTTPException(status.HTTP_409_CONFLICT, msg)
        if "no existe" in msg:
            raise HTTPException(status.HTTP_404_NOT_FOUND, msg)
        if "motor fallo" in msg or "no procesable" in msg.lower():
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, msg)
        raise HTTPException(status.HTTP_400_BAD_REQUEST, msg)
    except FingerprintEngineError as e:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"Motor: {e}")


# ── Verificacion ────────────────────────────────────────────────────────────

@router.post("/verify", response_model=VerifyResponse)
def post_verify(
    payload: VerifyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Verifica una captura contra todas las plantillas enroladas del empleado.
    1:1, no 1:N. matched=true si score >= MATCH_THRESHOLD (env, default 40)."""
    try:
        return fingerprint_service.verify_employee(
            db=db,
            employee_id=payload.employee_id,
            image_b64=payload.image_b64,
        )
    except ValueError as e:
        msg = str(e)
        if "no existe" in msg or "no tiene plantillas" in msg:
            raise HTTPException(status.HTTP_404_NOT_FOUND, msg)
        if "no procesable" in msg.lower():
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, msg)
        raise HTTPException(status.HTTP_400_BAD_REQUEST, msg)
    except FingerprintEngineError as e:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"Motor: {e}")


# ── Inventario por empleado ────────────────────────────────────────────────

@router.get("/employees/{employee_id}", response_model=EmployeeFingerprintsResponse)
def get_employee_fingerprints(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Lista plantillas enroladas (metadata, sin template_bytes) de un empleado."""
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Employee {employee_id} no existe")

    fingerprints = db.query(EmployeeFingerprint).filter(
        EmployeeFingerprint.employee_id == employee_id
    ).order_by(
        EmployeeFingerprint.finger_position,
        EmployeeFingerprint.capture_index
    ).all()

    return {
        "employee_id": employee.id,
        "employee_name": employee.full_name,
        "fingerprints": [
            FingerprintMetadata(
                id=fp.id,
                finger_position=fp.finger_position,
                capture_index=fp.capture_index,
                quality_score=fp.quality_score,
                created_at=fp.created_at,
                created_by=fp.created_by,
            ) for fp in fingerprints
        ],
        "total_captures": len(fingerprints),
    }


@router.delete("/employees/{employee_id}/{finger_position}",
               status_code=status.HTTP_204_NO_CONTENT)
def delete_employee_finger(
    employee_id: int,
    finger_position: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Elimina todas las capturas de un dedo de un empleado.
    404 si no habia plantillas. Ideal antes de re-enrolar."""
    try:
        deleted = fingerprint_service.delete_employee_finger(
            db=db,
            employee_id=employee_id,
            finger_position=finger_position,
            current_user=current_user,
        )
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))
    if deleted == 0:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No habia plantillas para ese dedo")
    return None


@router.get("/employees", response_model=List[EmployeeWithEnrollment])
def list_employees_with_enrollment(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_gestor),
):
    """Lista employees activos con su estado de enrolment.
    El gestor solo ve los de su delegacion (mas 'Ambas')."""
    q = db.query(Employee).filter(Employee.active == True)
    if current_user.role == "gestor":
        q = q.filter(Employee.delegacion.in_([current_user.delegacion, "Ambas"]))
    employees = q.order_by(Employee.full_name).all()
    result = []
    for emp in employees:
        fps = db.query(EmployeeFingerprint).filter(
            EmployeeFingerprint.employee_id == emp.id
        ).all()
        fingers = sorted(set(fp.finger_position for fp in fps))
        result.append(EmployeeWithEnrollment(
            employee_id=emp.id,
            full_name=emp.full_name,
            delegacion=emp.delegacion,
            user_id=emp.user_id,
            capture_count=len(fps),
            fingers_enrolled=fingers,
        ))
    return result


# ── Engine status ──────────────────────────────────────────────────────────

@router.get("/engine/status", response_model=EnginStatusResponse)
def get_engine_status(current_user: User = Depends(require_admin_or_gestor)):
    """Healthcheck del microservicio Java SourceAFIS."""
    engine = get_engine()
    try:
        health = engine.health_check()
        return EnginStatusResponse(
            healthy=True,
            version=health.get("version"),
            engine=health.get("engine"),
            uptime_seconds=health.get("uptime_seconds"),
        )
    except FingerprintEngineError as e:
        return EnginStatusResponse(healthy=False, error=str(e))


# ── Resolucion de metodo de firma para una contraparte ─────────────────────

@router.get("/signature-method", response_model=SignatureMethodResponse)
def get_signature_method(
    contraparte_type: str = Query(..., regex="^(supplier|employee|partner|free)$"),
    contraparte_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Determina que metodo de firma aplica para una contraparte dada.
    employee con enrolment -> fingerprint (con fallback a wacom).
    employee sin enrolment -> wacom_only_no_enrollment.
    supplier/partner/free -> wacom siempre."""
    try:
        return fingerprint_service.get_signature_method(db, contraparte_type, contraparte_id)
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))
