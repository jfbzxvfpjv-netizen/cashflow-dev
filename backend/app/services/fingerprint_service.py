"""
M11 Fingerprint - Logica de negocio.
Wrapper sobre fingerprint_engine + SQLAlchemy.
"""
import base64
import os
from typing import Optional, List
from sqlalchemy.orm import Session

from app.models.cash_flow import EmployeeFingerprint
from app.models.catalogs import Employee, Supplier
from app.models.user import User
from app.models.audit_log import AuditLog
from app.services.fingerprint_engine import get_engine, FingerprintEngineError
from app.services import dp_format


# Configuracion via env
MATCH_THRESHOLD = int(os.getenv("FINGERPRINT_MATCH_THRESHOLD", "40"))
ENROLL_MIN_QUALITY = int(os.getenv("FINGERPRINT_ENROLL_MIN_QUALITY", "60"))


VALID_FINGER_POSITIONS = {
    'right_thumb', 'right_index', 'right_middle', 'right_ring', 'right_pinky',
    'left_thumb', 'left_index', 'left_middle', 'left_ring', 'left_pinky',
}


def _safe_b64decode(s: str, label: str = "image_b64") -> bytes:
    """Decodifica image_b64 a bytes procesables por SourceAFIS.

    Detecta automaticamente envelope DigitalPersona Raw (estructura
    base64(JSON{Compression, Data})) y lo convierte a PNG via dp_format.
    Si no es DP, sigue como base64 estandar (PNG ya proporcionado, dummy
    de test, etc).
    """
    # Intentar conversion DP -> PNG si el contenido es envelope DigitalPersona
    try:
        png_bytes = dp_format.try_convert_dp_to_png(s)
        if png_bytes is not None:
            return png_bytes
    except Exception:
        # No es DP o conversion fallo; caer al flujo base64 estandar
        pass
    try:
        return base64.b64decode(s)
    except Exception:
        raise ValueError(f"{label} no es base64 valido")


def assess_quality(image_b64: str) -> dict:
    """Extrae template solo para reportar calidad. No persiste nada."""
    image_bytes = _safe_b64decode(image_b64)
    engine = get_engine()
    try:
        _, quality_score, minutiae_count = engine.extract_template(image_bytes)
    except FingerprintEngineError as e:
        if "Image not processable" in str(e):
            return {"quality_score": 0, "minutiae_count": 0, "has_minutiae": False}
        raise
    return {
        "quality_score": int(quality_score),
        "minutiae_count": int(minutiae_count),
        "has_minutiae": minutiae_count >= 12,
    }


def enroll_employee_finger(
    db: Session,
    employee_id: int,
    finger_position: str,
    images_b64: List[str],
    current_user: User
) -> dict:
    """Enrola las 4 capturas de un dedo de un empleado. Atomico: o todas o ninguna."""
    if finger_position not in VALID_FINGER_POSITIONS:
        raise ValueError(f"finger_position invalido: {finger_position}")
    if len(images_b64) != 4:
        raise ValueError("Se requieren exactamente 4 imagenes")

    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise ValueError(f"Employee {employee_id} no existe")

    # Verificar que no esta ya enrolado este dedo
    existing = db.query(EmployeeFingerprint).filter(
        EmployeeFingerprint.employee_id == employee_id,
        EmployeeFingerprint.finger_position == finger_position
    ).count()
    if existing > 0:
        raise ValueError(
            f"Dedo {finger_position} ya esta enrolado para empleado {employee_id}. "
            f"Eliminar primero las {existing} capturas existentes.")

    # Procesar las 4 imagenes (extraer templates antes de persistir nada)
    engine = get_engine()
    extracted = []
    for idx, img_b64 in enumerate(images_b64):
        image_bytes = _safe_b64decode(img_b64, f"images_b64[{idx}]")
        try:
            template, quality, _minutiae = engine.extract_template(image_bytes)
        except FingerprintEngineError as e:
            raise ValueError(f"Captura #{idx+1}: motor fallo: {e}")
        extracted.append((idx + 1, template, int(quality)))

    # Persistir las 4
    enrolled_results = []
    for capture_index, template_bytes, quality_score in extracted:
        fp = EmployeeFingerprint(
            employee_id=employee_id,
            finger_position=finger_position,
            capture_index=capture_index,
            template_bytes=template_bytes,
            quality_score=quality_score,
            created_by=current_user.id,
        )
        db.add(fp)
        enrolled_results.append({
            "capture_index": capture_index,
            "quality_score": quality_score,
        })

    # Audit log
    avg_quality = sum(q for _, _, q in extracted) // 4
    db.add(AuditLog(
        user_id=current_user.id,
        action="fingerprint_enroll",
        entity="employee_fingerprints",
        entity_id=employee_id,
        details={
            "employee_id": employee_id,
            "employee_name": employee.full_name,
            "finger_position": finger_position,
            "captures": 4,
            "quality_avg": avg_quality,
        }
    ))

    db.commit()
    return {
        "employee_id": employee_id,
        "finger_position": finger_position,
        "enrolled": enrolled_results,
    }


def verify_employee(db: Session, employee_id: int, image_b64: str) -> dict:
    """Verifica una captura contra todas las plantillas enroladas del empleado.
    1:1, no 1:N. Devuelve mejor score y dedo correspondiente."""
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise ValueError(f"Employee {employee_id} no existe")

    fingerprints = db.query(EmployeeFingerprint).filter(
        EmployeeFingerprint.employee_id == employee_id
    ).all()
    if not fingerprints:
        raise ValueError(f"Employee {employee_id} no tiene plantillas enroladas")

    image_bytes = _safe_b64decode(image_b64)
    engine = get_engine()

    try:
        new_template, _q, _m = engine.extract_template(image_bytes)
    except FingerprintEngineError as e:
        raise ValueError(f"Imagen no procesable: {e}")

    best_score = 0.0
    best_finger = None
    for fp in fingerprints:
        try:
            score = engine.match_templates(fp.template_bytes, new_template)
        except FingerprintEngineError:
            continue
        if score > best_score:
            best_score = score
            best_finger = fp.finger_position

    return {
        "matched": best_score >= MATCH_THRESHOLD,
        "score": round(best_score, 2),
        "finger_position": best_finger if best_score >= MATCH_THRESHOLD else None,
        "threshold": MATCH_THRESHOLD,
    }


def delete_employee_finger(
    db: Session,
    employee_id: int,
    finger_position: str,
    current_user: User
) -> int:
    """Elimina todas las capturas de un dedo. Devuelve numero eliminado."""
    if finger_position not in VALID_FINGER_POSITIONS:
        raise ValueError(f"finger_position invalido: {finger_position}")

    deleted = db.query(EmployeeFingerprint).filter(
        EmployeeFingerprint.employee_id == employee_id,
        EmployeeFingerprint.finger_position == finger_position
    ).delete()

    if deleted > 0:
        db.add(AuditLog(
            user_id=current_user.id,
            action="fingerprint_delete",
            entity="employee_fingerprints",
            entity_id=employee_id,
            details={
                "employee_id": employee_id,
                "finger_position": finger_position,
                "captures_deleted": deleted,
            }
        ))
        db.commit()

    return deleted


def get_signature_method(
    db: Session,
    contraparte_type: str,
    contraparte_id: Optional[int]
) -> dict:
    """Determina que metodo de firma aplica segun la contraparte:
    - employee con enrolment -> fingerprint (con fallback a wacom)
    - employee sin enrolment -> wacom_only_no_enrollment
    - supplier/partner/free -> wacom (siempre)
    """
    if contraparte_type == "supplier":
        supplier = db.query(Supplier).filter(Supplier.id == contraparte_id).first() if contraparte_id else None
        return {
            "method": "wacom",
            "signer_name": supplier.name if supplier else "?",
            "employee_id": None,
            "has_enrollment": False,
            "fallback_method": None,
        }

    if contraparte_type in ("partner", "free"):
        return {
            "method": "wacom",
            "signer_name": "(socio)" if contraparte_type == "partner" else "?",
            "employee_id": None,
            "has_enrollment": False,
            "fallback_method": None,
        }

    if contraparte_type == "employee":
        if contraparte_id is None:
            raise ValueError("contraparte_id requerido para type=employee")
        employee = db.query(Employee).filter(Employee.id == contraparte_id).first()
        if not employee:
            raise ValueError(f"Employee {contraparte_id} no existe")

        has_enrollment = db.query(EmployeeFingerprint).filter(
            EmployeeFingerprint.employee_id == contraparte_id
        ).count() > 0

        if has_enrollment:
            return {
                "method": "fingerprint",
                "signer_name": employee.full_name,
                "employee_id": employee.id,
                "has_enrollment": True,
                "fallback_method": "wacom",
            }
        return {
            "method": "wacom_only_no_enrollment",
            "signer_name": employee.full_name,
            "employee_id": employee.id,
            "has_enrollment": False,
            "fallback_method": "wacom",
        }

    raise ValueError(f"contraparte_type desconocido: {contraparte_type}")
