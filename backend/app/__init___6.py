"""
Paquete models — Importa todos los modelos para registro en SQLAlchemy.

Al importar este paquete, todos los modelos quedan registrados en Base.metadata
y pueden crearse con Base.metadata.create_all(engine).
"""

from app.models.user import User
from app.models.audit_log import AuditLog

__all__ = ["User", "AuditLog"]
