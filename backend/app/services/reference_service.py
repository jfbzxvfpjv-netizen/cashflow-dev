"""
Referencias secuenciales: B0001-B9999 / M0001-M9999.
"""
from sqlalchemy import text
from sqlalchemy.orm import Session


def generate_reference(db: Session, delegacion: str) -> str:
    prefix = "B" if delegacion == "Bata" else "M"
    result = db.execute(
        text("SELECT reference_number FROM transactions "
             "WHERE delegacion = :d ORDER BY id DESC LIMIT 1 FOR UPDATE"),
        {"d": delegacion},
    ).fetchone()
    last_num = 0
    if result and result[0]:
        try:
            last_num = int(result[0][1:])
        except (ValueError, IndexError):
            pass
    next_num = last_num + 1
    if next_num > 9999:
        raise ValueError(f"Límite de 9999 referencias superado para {delegacion}")
    return f"{prefix}{next_num:04d}"
