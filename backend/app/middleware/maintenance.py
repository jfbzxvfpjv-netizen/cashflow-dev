"""
Middleware de modo mantenimiento.
Módulo M8b — Bloquea peticiones durante la restauración de backups.

Cuando el sistema está en modo mantenimiento (flag en disco activado
por el proceso de restauración), todas las peticiones que no sean al
propio endpoint de backups reciben HTTP 503.
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from app.services.backup_service import BackupService


class MaintenanceMiddleware(BaseHTTPMiddleware):
    """Rechaza peticiones cuando hay una restauración en curso."""

    async def dispatch(self, request: Request, call_next):
        if BackupService.is_maintenance_mode():
            # Permitir acceso a los endpoints de backups y health
            path = request.url.path
            if not (
                path.startswith("/api/v1/admin/backups")
                or path == "/health"
                or path == "/api/v1/health"
            ):
                return JSONResponse(
                    status_code=503,
                    content={
                        "detail": (
                            "Sistema en modo mantenimiento. "
                            "Restauración de backup en curso. "
                            "Espere a que finalice el proceso."
                        )
                    },
                )
        return await call_next(request)
