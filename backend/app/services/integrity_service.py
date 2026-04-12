"""
Integridad — Hash SHA-256 por transacción.
"""
import hashlib


def compute_transaction_hash(tx) -> str:
    payload = (
        f"{tx.id}|{tx.reference_number}|{tx.session_id}|{tx.delegacion}|"
        f"{tx.user_id}|{tx.type}|{format(float(tx.amount), '.2f')}|"
        f"{tx.concept}|{tx.category_id}|{tx.subcategory_id}|"
        f"{tx.created_at.isoformat()}"
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def verify_transaction_hash(tx) -> bool:
    return tx.integrity_hash == compute_transaction_hash(tx)
