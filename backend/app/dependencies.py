"""
Módulo de compatibilidad — Re-exporta las dependencias de autenticación
desde app.core.deps para que los routers del M4 funcionen sin modificar
sus imports. También exporta get_db.
"""

from app.core.deps import get_current_user, require_role  # noqa: F401
from app.database import SessionLocal


def get_db():
    """Genera una sesión de BD y la cierra al terminar."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
