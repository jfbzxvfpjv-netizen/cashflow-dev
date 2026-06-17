"""M11 — persistencia de firma inline colgada de una transaccion.
Replica el contrato de transaction_service.create_transaction (lineas 258-330).
No hace commit; consolida el llamante. Reutilizable por modulos M9."""
import base64
import hashlib
from sqlalchemy.orm import Session
from app.models.cash_flow import TransactionSignature
from app.models.catalogs import Employee


def persist_inline_signature(db: Session, txn, sig: dict, captured_by_user_id: int):
    if not sig:
        raise ValueError("Firma requerida")
    method = sig.get("signature_method", "wacom")
    if method in ("wacom", "wacom_provisional"):
        if not sig.get("signature_data"):
            raise ValueError("signature.signature_data requerido para method=wacom")
        try:
            png = base64.b64decode(sig["signature_data"])
        except Exception:
            raise ValueError("signature_data no es base64 valido")
        fss = None
        if sig.get("fss_data_b64"):
            try:
                fss = base64.b64decode(sig["fss_data_b64"])
            except Exception:
                raise ValueError("fss_data_b64 no es base64 valido")
        row = TransactionSignature(
            transaction_id=txn.id,
            signer_type=sig["signer_type"],
            signer_name=sig["signer_name"],
            signature_data=sig["signature_data"],
            status=sig.get("status") or "valid",
            employee_id=sig.get("employee_id"),
            supplier_id=sig.get("supplier_id"),
            partner_id=sig.get("partner_id"),
            sha256_hash=hashlib.sha256(png).hexdigest(),
            device_model=sig.get("device_model"),
            width_px=sig.get("width_px"),
            height_px=sig.get("height_px"),
            duration_ms=sig.get("duration_ms"),
            fss_data=fss,
            captured_by_user_id=captured_by_user_id,
            signature_method=method,
            fingerprint_failed_scores=sig.get("fingerprint_failed_scores"),
        )
    elif method == "fingerprint":
        if sig.get("fingerprint_score") is None:
            raise ValueError("signature.fingerprint_score requerido para method=fingerprint")
        if not sig.get("fingerprint_finger_position"):
            raise ValueError("signature.fingerprint_finger_position requerido para method=fingerprint")
        suid = sig.get("signer_user_id")
        if not suid and sig.get("employee_id"):
            emp = db.query(Employee).filter(Employee.id == sig["employee_id"]).first()
            if emp and emp.user_id:
                suid = emp.user_id
        if not suid:
            raise ValueError("signature.signer_user_id no resuelto (employee sin user vinculado)")
        row = TransactionSignature(
            transaction_id=txn.id,
            signer_type=sig["signer_type"],
            signer_name=sig["signer_name"],
            signature_method="fingerprint",
            employee_id=sig.get("employee_id"),
            supplier_id=sig.get("supplier_id"),
            partner_id=sig.get("partner_id"),
            captured_by_user_id=captured_by_user_id,
            fingerprint_score=sig["fingerprint_score"],
            fingerprint_finger_position=sig["fingerprint_finger_position"],
            fingerprint_attempts=sig.get("fingerprint_attempts", 1),
            signer_user_id=suid,
            status="valid",
        )
    else:
        raise ValueError(f"signature_method desconocido: {method}")
    db.add(row)
    return row
