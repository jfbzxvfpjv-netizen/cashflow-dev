#!/bin/bash
set -euo pipefail

# ============================================================
# MÓDULO M8b — Panel de Gestión de Backups PostgreSQL
# Caja R2i — Gestión de Flujo de Caja
# ============================================================
# Módulo independiente de la Capa 1. Solo perfil Administrador.
# Backup automático diario con pg_dump + cron dentro del
# contenedor db, retención de 30 días, panel de administración
# con backup manual, descarga, restauración guiada y eliminación.
#
# Ficheros existentes modificados (solo dos):
#   - docker-compose.yml  → volumen backups-dev, mounts y entrypoints
#   - backend/app/main.py → registro del router admin_backups
#   - frontend/src/router/index.js → ruta /admin/backups
#
# Ejecutar desde la raíz del proyecto:
#   chmod +x m8b_backups.sh && ./m8b_backups.sh
# ============================================================

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "============================================================"
echo "  M8b — Gestión de Backups PostgreSQL"
echo "  $(date)"
echo "============================================================"

# ────────────────────────────────────────────────────────────
# 1. BACKUP DE FICHEROS EXISTENTES
# ────────────────────────────────────────────────────────────
echo ""
echo "[1/9] Creando backups de ficheros existentes..."

cp "$PROJECT_ROOT/docker-compose.yml" \
   "$PROJECT_ROOT/docker-compose.yml.bak.$TIMESTAMP"
echo "  → docker-compose.yml.bak.$TIMESTAMP"

if [ -f "$PROJECT_ROOT/backend/app/main.py" ]; then
    cp "$PROJECT_ROOT/backend/app/main.py" \
       "$PROJECT_ROOT/backend/app/main.py.bak.$TIMESTAMP"
    echo "  → backend/app/main.py.bak.$TIMESTAMP"
fi

if [ -f "$PROJECT_ROOT/frontend/src/router/index.js" ]; then
    cp "$PROJECT_ROOT/frontend/src/router/index.js" \
       "$PROJECT_ROOT/frontend/src/router/index.js.bak.$TIMESTAMP"
    echo "  → frontend/src/router/index.js.bak.$TIMESTAMP"
fi

# ────────────────────────────────────────────────────────────
# 2. SCRIPTS DE BACKUP Y CRON (contenedor db)
# ────────────────────────────────────────────────────────────
echo ""
echo "[2/9] Creando scripts de backup y cron..."

mkdir -p "$PROJECT_ROOT/scripts"

# --- backup_db.sh: ejecutado por cron y disponible para invocación manual ---
cat > "$PROJECT_ROOT/scripts/backup_db.sh" << 'EOF'
#!/bin/sh
# ──────────────────────────────────────────────────────────
# backup_db.sh — Backup PostgreSQL con pg_dump
# Se ejecuta dentro del contenedor db vía cron (02:00 diario)
# y también bajo demanda desde la API.
# Retención automática: elimina backups con más de 30 días.
# ──────────────────────────────────────────────────────────

BACKUP_DIR="/backups"
DB_NAME="${POSTGRES_DB:-cashflow_dev}"
DB_USER="${POSTGRES_USER:-postgres}"
RETENTION_DAYS=30
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
FILENAME="${DB_NAME}_${TIMESTAMP}.dump"

mkdir -p "$BACKUP_DIR"

echo "[$(date)] Iniciando backup de ${DB_NAME}..."

pg_dump -U "$DB_USER" -d "$DB_NAME" -F c -Z 6 -f "${BACKUP_DIR}/${FILENAME}"

if [ $? -eq 0 ]; then
    SIZE=$(du -h "${BACKUP_DIR}/${FILENAME}" | cut -f1)
    echo "[$(date)] Backup completado: ${FILENAME} (${SIZE})"
else
    echo "[$(date)] ERROR: Fallo en el backup de ${DB_NAME}"
    exit 1
fi

# Limpieza de backups antiguos (retención 30 días)
DELETED=$(find "$BACKUP_DIR" -name "${DB_NAME}_*.dump" -mtime +${RETENTION_DAYS} -print -delete | wc -l)
if [ "$DELETED" -gt 0 ]; then
    echo "[$(date)] Limpieza: ${DELETED} backup(s) con más de ${RETENTION_DAYS} días eliminados"
fi
EOF
chmod +x "$PROJECT_ROOT/scripts/backup_db.sh"
echo "  → scripts/backup_db.sh"

# --- db_entrypoint.sh: wrapper del entrypoint de PostgreSQL ---
# Configura cron antes de arrancar postgres
cat > "$PROJECT_ROOT/scripts/db_entrypoint.sh" << 'EOF'
#!/bin/sh
# ──────────────────────────────────────────────────────────
# db_entrypoint.sh — Wrapper del entrypoint de PostgreSQL
# Configura el cron de backup diario y luego ejecuta
# el entrypoint original de postgres:15-alpine.
# ──────────────────────────────────────────────────────────

# Configurar cron para backup diario a las 02:00
echo "0 2 * * * /usr/local/bin/backup_db.sh >> /var/log/backup_cron.log 2>&1" | crontab -

# Arrancar cron en segundo plano
crond -b -l 8

echo "[db_entrypoint] Cron de backup configurado (02:00 diario)"

# Ejecutar el entrypoint original de PostgreSQL
exec docker-entrypoint.sh "$@"
EOF
chmod +x "$PROJECT_ROOT/scripts/db_entrypoint.sh"
echo "  → scripts/db_entrypoint.sh"

# --- backend_entrypoint.sh: instala postgresql-client en el backend ---
# Necesario para que el backend pueda ejecutar pg_dump/pg_restore
# directamente contra la base de datos vía red Docker.
cat > "$PROJECT_ROOT/scripts/backend_entrypoint.sh" << 'EOF'
#!/bin/bash
# ──────────────────────────────────────────────────────────
# backend_entrypoint.sh — Wrapper del entrypoint del backend
# Instala postgresql-client (pg_dump, pg_restore, psql) si
# no está disponible. Necesario para el módulo M8b de backups.
# ──────────────────────────────────────────────────────────

if ! command -v pg_dump &> /dev/null; then
    echo "[backend_entrypoint] Instalando postgresql-client para backups..."
    apt-get update -qq > /dev/null 2>&1
    apt-get install -y -qq --no-install-recommends postgresql-client > /dev/null 2>&1
    rm -rf /var/lib/apt/lists/*
    echo "[backend_entrypoint] postgresql-client instalado"
fi

exec "$@"
EOF
chmod +x "$PROJECT_ROOT/scripts/backend_entrypoint.sh"
echo "  → scripts/backend_entrypoint.sh"

# ────────────────────────────────────────────────────────────
# 3. SERVICIO DE BACKUPS (backend)
# ────────────────────────────────────────────────────────────
echo ""
echo "[3/9] Creando servicio de backups..."

mkdir -p "$PROJECT_ROOT/backend/app/services"

cat > "$PROJECT_ROOT/backend/app/services/backup_service.py" << 'PYEOF'
"""
Servicio de gestión de backups PostgreSQL.
Módulo M8b — Backup, restauración, descarga y eliminación.
Todas las operaciones de pg_dump/pg_restore se ejecutan desde
el backend contra la base de datos vía la red Docker interna.
"""

import os
import re
import glob
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional

# Directorio del volumen compartido de backups
BACKUP_DIR = os.getenv("BACKUP_DIR", "/backups")

# Conexión a la base de datos (mismas variables que usa el backend)
DB_HOST = os.getenv("POSTGRES_HOST", "db")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_NAME = os.getenv("POSTGRES_DB", "cashflow_dev")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "")

# Fichero de flag para modo mantenimiento durante restauración
MAINTENANCE_FLAG = os.path.join(BACKUP_DIR, ".maintenance_mode")

# Patrón válido para nombres de fichero de backup
FILENAME_PATTERN = re.compile(r'^[a-zA-Z0-9_\-]+\.dump$')


class BackupError(Exception):
    """Error específico de operaciones de backup."""
    pass


class BackupService:
    """Gestiona el ciclo de vida de los backups PostgreSQL."""

    def __init__(self):
        os.makedirs(BACKUP_DIR, exist_ok=True)

    # ── Validación ────────────────────────────────────────

    def _validate_filename(self, filename: str) -> str:
        """Valida el nombre de fichero para prevenir path traversal."""
        if not filename or ".." in filename or "/" in filename or "\\" in filename:
            raise BackupError("Nombre de fichero no válido")
        if not FILENAME_PATTERN.match(filename):
            raise BackupError("Formato de nombre de fichero no permitido")
        return os.path.join(BACKUP_DIR, filename)

    def _get_pgenv(self) -> dict:
        """Devuelve las variables de entorno para los comandos pg_*."""
        env = os.environ.copy()
        env["PGPASSWORD"] = DB_PASSWORD
        return env

    # ── Listar backups ────────────────────────────────────

    def list_backups(self) -> dict:
        """
        Lista todos los backups disponibles ordenados por fecha
        descendente. Devuelve nombre, tamaño en bytes y MB, y
        fecha de creación extraída del timestamp del fichero.
        """
        backups = []
        pattern = os.path.join(BACKUP_DIR, f"{DB_NAME}_*.dump")

        for filepath in glob.glob(pattern):
            stat = os.stat(filepath)
            backups.append({
                "filename": os.path.basename(filepath),
                "size_bytes": stat.st_size,
                "size_mb": round(stat.st_size / (1024 * 1024), 2),
                "created_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            })

        backups.sort(key=lambda b: b["created_at"], reverse=True)
        return {"backups": backups, "total": len(backups)}

    # ── Crear backup ──────────────────────────────────────

    def create_backup(self) -> dict:
        """
        Genera un backup manual inmediato con pg_dump en formato
        custom comprimido (nivel 6). El fichero se nombra con
        timestamp al segundo para evitar colisiones.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{DB_NAME}_{timestamp}.dump"
        filepath = os.path.join(BACKUP_DIR, filename)

        result = subprocess.run(
            [
                "pg_dump",
                "-h", DB_HOST,
                "-p", DB_PORT,
                "-U", DB_USER,
                "-d", DB_NAME,
                "-F", "c",
                "-Z", "6",
                "-f", filepath,
            ],
            env=self._get_pgenv(),
            capture_output=True,
            text=True,
            timeout=600,
        )

        if result.returncode != 0:
            # Limpiar fichero parcial si existe
            if os.path.exists(filepath):
                os.remove(filepath)
            raise BackupError(f"Error al crear backup: {result.stderr.strip()}")

        stat = os.stat(filepath)
        return {
            "message": "Backup creado correctamente",
            "filename": filename,
            "size_bytes": stat.st_size,
            "size_mb": round(stat.st_size / (1024 * 1024), 2),
            "created_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        }

    # ── Obtener ruta de backup ────────────────────────────

    def get_backup_path(self, filename: str) -> Optional[str]:
        """Devuelve la ruta absoluta del backup si existe."""
        filepath = self._validate_filename(filename)
        if os.path.isfile(filepath):
            return filepath
        return None

    # ── Restaurar backup ──────────────────────────────────

    def restore_backup(self, filename: str) -> dict:
        """
        Restaura la base de datos desde un backup.

        Proceso:
        1. Activa modo mantenimiento (flag en disco).
        2. Termina todas las conexiones activas a la BD.
        3. Elimina y recrea la base de datos.
        4. Ejecuta pg_restore desde el fichero seleccionado.
        5. Desactiva modo mantenimiento.

        Si cualquier paso falla, el modo mantenimiento se
        desactiva igualmente para no bloquear el sistema.
        Se recomienda reiniciar los contenedores tras la
        restauración para restablecer los pools de conexión.
        """
        filepath = self.get_backup_path(filename)
        if not filepath:
            raise BackupError("Backup no encontrado")

        # Activar modo mantenimiento
        Path(MAINTENANCE_FLAG).touch()
        env = self._get_pgenv()

        try:
            # Paso 1: Terminar conexiones activas
            subprocess.run(
                [
                    "psql",
                    "-h", DB_HOST,
                    "-p", DB_PORT,
                    "-U", DB_USER,
                    "-d", "postgres",
                    "-c",
                    f"SELECT pg_terminate_backend(pid) "
                    f"FROM pg_stat_activity "
                    f"WHERE datname = '{DB_NAME}' "
                    f"AND pid <> pg_backend_pid();",
                ],
                env=env,
                capture_output=True,
                text=True,
                timeout=30,
            )

            # Paso 2: Eliminar la base de datos
            drop_result = subprocess.run(
                [
                    "dropdb",
                    "-h", DB_HOST,
                    "-p", DB_PORT,
                    "-U", DB_USER,
                    "--if-exists",
                    DB_NAME,
                ],
                env=env,
                capture_output=True,
                text=True,
                timeout=30,
            )
            if drop_result.returncode != 0:
                raise BackupError(
                    f"Error al eliminar la BD: {drop_result.stderr.strip()}"
                )

            # Paso 3: Recrear la base de datos vacía
            create_result = subprocess.run(
                [
                    "createdb",
                    "-h", DB_HOST,
                    "-p", DB_PORT,
                    "-U", DB_USER,
                    DB_NAME,
                ],
                env=env,
                capture_output=True,
                text=True,
                timeout=30,
            )
            if create_result.returncode != 0:
                raise BackupError(
                    f"Error al crear la BD: {create_result.stderr.strip()}"
                )

            # Paso 4: Restaurar desde el backup
            restore_result = subprocess.run(
                [
                    "pg_restore",
                    "-h", DB_HOST,
                    "-p", DB_PORT,
                    "-U", DB_USER,
                    "-d", DB_NAME,
                    "--no-owner",
                    "--no-privileges",
                    "--single-transaction",
                    filepath,
                ],
                env=env,
                capture_output=True,
                text=True,
                timeout=900,
            )

            # pg_restore devuelve 1 para warnings (no fatales)
            if restore_result.returncode > 1:
                raise BackupError(
                    f"Error en la restauración: {restore_result.stderr.strip()}"
                )

            return {
                "message": (
                    "Base de datos restaurada correctamente desde "
                    f"'{filename}'. Se recomienda reiniciar los "
                    "contenedores con: docker compose restart backend"
                ),
                "filename": filename,
                "requires_restart": True,
                "warnings": restore_result.stderr.strip() or None,
            }

        finally:
            # Desactivar modo mantenimiento siempre
            if os.path.exists(MAINTENANCE_FLAG):
                os.remove(MAINTENANCE_FLAG)

    # ── Eliminar backup ───────────────────────────────────

    def delete_backup(self, filename: str) -> dict:
        """Elimina un fichero de backup del volumen."""
        filepath = self.get_backup_path(filename)
        if not filepath:
            raise BackupError("Backup no encontrado")
        os.remove(filepath)
        return {
            "message": f"Backup '{filename}' eliminado correctamente",
            "filename": filename,
        }

    # ── Modo mantenimiento ────────────────────────────────

    @staticmethod
    def is_maintenance_mode() -> bool:
        """Comprueba si el sistema está en modo mantenimiento."""
        return os.path.exists(MAINTENANCE_FLAG)
PYEOF
echo "  → backend/app/services/backup_service.py"

# ────────────────────────────────────────────────────────────
# 4. MIDDLEWARE DE MODO MANTENIMIENTO (backend)
# ────────────────────────────────────────────────────────────
echo ""
echo "[4/9] Creando middleware de mantenimiento..."

mkdir -p "$PROJECT_ROOT/backend/app/middleware"

# Crear __init__.py si no existe
touch "$PROJECT_ROOT/backend/app/middleware/__init__.py"

cat > "$PROJECT_ROOT/backend/app/middleware/maintenance.py" << 'PYEOF'
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
PYEOF
echo "  → backend/app/middleware/maintenance.py"

# ────────────────────────────────────────────────────────────
# 5. ROUTER DE BACKUPS (backend)
# ────────────────────────────────────────────────────────────
echo ""
echo "[5/9] Creando router de backups..."

mkdir -p "$PROJECT_ROOT/backend/app/routers"

cat > "$PROJECT_ROOT/backend/app/routers/admin_backups.py" << 'PYEOF'
"""
Router de gestión de backups PostgreSQL.
Módulo M8b — Endpoints exclusivos para el perfil Administrador.

Endpoints:
  GET    /admin/backups                      → Lista backups
  POST   /admin/backups                      → Backup manual
  GET    /admin/backups/{filename}/download   → Descarga backup
  POST   /admin/backups/{filename}/restore    → Restauración guiada
  DELETE /admin/backups/{filename}            → Elimina backup
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.deps import require_role
from app.database import SessionLocal
from app.services.backup_service import BackupService, BackupError

router = APIRouter(prefix="/admin/backups", tags=["backups"])


# ── Esquemas ──────────────────────────────────────────────

class RestoreRequest(BaseModel):
    """Cuerpo de la petición de restauración con confirmación explícita."""
    confirmation: str = Field(
        ...,
        description="Debe ser exactamente 'RESTAURAR' para confirmar"
    )


# ── Dependencia de base de datos ──────────────────────────

def get_db():
    """Genera una sesión de base de datos para audit logging."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── Helpers de auditoría ──────────────────────────────────

def _audit_log(
    db: Session,
    user_id: int,
    action: str,
    details: dict = None,
    ip_address: str = None,
):
    """Registra una operación de backup en el log de auditoría."""
    try:
        from app.models.audit import AuditLog
        log = AuditLog(
            user_id=user_id,
            action=action,
            entity="backup",
            entity_id=None,
            details=details,
            ip_address=ip_address,
            access_type="local",
        )
        db.add(log)
        db.commit()
    except Exception:
        # No bloquear la operación si falla el audit
        db.rollback()


def _get_client_ip(request: Request) -> str:
    """Obtiene la IP del cliente de la petición."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


# ── Endpoints ─────────────────────────────────────────────

@router.get("")
def list_backups(current_user=Depends(require_role("admin"))):
    """
    Lista todos los backups disponibles en el volumen de backups.
    Devuelve nombre, tamaño y fecha de cada fichero, ordenados
    por fecha descendente.
    """
    service = BackupService()
    return service.list_backups()


@router.post("", status_code=status.HTTP_201_CREATED)
def create_backup(
    request: Request,
    current_user=Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """
    Genera un backup manual inmediato con pg_dump. El fichero
    se guarda en el volumen de backups con timestamp al segundo.
    """
    try:
        service = BackupService()
        result = service.create_backup()
        _audit_log(
            db,
            user_id=current_user.id,
            action="BACKUP_CREATED",
            details={"filename": result["filename"], "size_mb": result["size_mb"]},
            ip_address=_get_client_ip(request),
        )
        return result
    except BackupError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{filename}/download")
def download_backup(
    filename: str,
    request: Request,
    current_user=Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """
    Descarga el fichero de backup indicado. El nombre del fichero
    se valida para prevenir ataques de path traversal.
    """
    service = BackupService()
    filepath = service.get_backup_path(filename)
    if not filepath:
        raise HTTPException(status_code=404, detail="Backup no encontrado")

    _audit_log(
        db,
        user_id=current_user.id,
        action="BACKUP_DOWNLOADED",
        details={"filename": filename},
        ip_address=_get_client_ip(request),
    )
    return FileResponse(
        path=filepath,
        filename=filename,
        media_type="application/octet-stream",
    )


@router.post("/{filename}/restore")
def restore_backup(
    filename: str,
    body: RestoreRequest,
    request: Request,
    current_user=Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """
    Restaura la base de datos desde el backup indicado.

    El proceso activa el modo mantenimiento, elimina la BD actual,
    la recrea y ejecuta pg_restore. Requiere confirmación explícita
    escribiendo 'RESTAURAR'. Tras la restauración se recomienda
    reiniciar el contenedor backend.
    """
    if body.confirmation != "RESTAURAR":
        raise HTTPException(
            status_code=400,
            detail="Debe escribir exactamente 'RESTAURAR' para confirmar la restauración",
        )

    _audit_log(
        db,
        user_id=current_user.id,
        action="RESTORE_STARTED",
        details={"filename": filename},
        ip_address=_get_client_ip(request),
    )

    try:
        service = BackupService()
        result = service.restore_backup(filename)

        # Nota: tras la restauración el pool de conexiones puede estar
        # roto, por lo que este audit podría fallar. Es esperado.
        try:
            db_new = SessionLocal()
            _audit_log(
                db_new,
                user_id=current_user.id,
                action="RESTORE_COMPLETED",
                details={"filename": filename},
                ip_address=_get_client_ip(request),
            )
            db_new.close()
        except Exception:
            pass

        return result

    except BackupError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{filename}")
def delete_backup(
    filename: str,
    request: Request,
    current_user=Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """
    Elimina un fichero de backup del volumen. La eliminación
    es irreversible — el fichero se borra del disco.
    """
    try:
        service = BackupService()
        result = service.delete_backup(filename)
        _audit_log(
            db,
            user_id=current_user.id,
            action="BACKUP_DELETED",
            details={"filename": filename},
            ip_address=_get_client_ip(request),
        )
        return result
    except BackupError as e:
        raise HTTPException(
            status_code=404 if "no encontrado" in str(e).lower() else 500,
            detail=str(e),
        )
PYEOF
echo "  → backend/app/routers/admin_backups.py"

# ────────────────────────────────────────────────────────────
# 6. VISTA FRONTEND — BackupsView.vue
# ────────────────────────────────────────────────────────────
echo ""
echo "[6/9] Creando vista frontend de backups..."

mkdir -p "$PROJECT_ROOT/frontend/src/views/admin"

cat > "$PROJECT_ROOT/frontend/src/views/admin/BackupsView.vue" << 'VUEEOF'
<template>
  <div class="max-w-5xl mx-auto px-4 py-6">
    <!-- Cabecera -->
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-800">Gestión de Backups</h1>
        <p class="text-sm text-gray-500 mt-1">
          Backups de la base de datos PostgreSQL — Retención automática 30 días
        </p>
      </div>
      <button
        @click="createBackup"
        :disabled="creating"
        class="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg
               hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed
               transition-colors text-sm font-medium"
      >
        <svg v-if="creating" class="animate-spin -ml-1 mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"/>
        </svg>
        <svg v-else class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M12 4v16m8-8H4"/>
        </svg>
        {{ creating ? 'Creando backup...' : 'Crear Backup Manual' }}
      </button>
    </div>

    <!-- Mensaje de estado -->
    <div v-if="statusMessage"
         :class="[
           'mb-4 px-4 py-3 rounded-lg text-sm',
           statusType === 'success' ? 'bg-green-50 text-green-800 border border-green-200' :
           statusType === 'error' ? 'bg-red-50 text-red-800 border border-red-200' :
           'bg-blue-50 text-blue-800 border border-blue-200'
         ]">
      {{ statusMessage }}
    </div>

    <!-- Tabla de backups -->
    <div class="bg-white rounded-lg shadow overflow-hidden">
      <div v-if="loading" class="p-8 text-center text-gray-500">
        <svg class="animate-spin h-8 w-8 mx-auto mb-3 text-blue-500" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"/>
        </svg>
        Cargando backups...
      </div>

      <div v-else-if="backups.length === 0" class="p-8 text-center text-gray-500">
        <svg class="w-12 h-12 mx-auto mb-3 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
                d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8"/>
        </svg>
        No hay backups disponibles. Cree uno con el botón superior.
      </div>

      <table v-else class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <th class="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
              Fichero
            </th>
            <th class="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
              Fecha
            </th>
            <th class="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase tracking-wider">
              Tamaño
            </th>
            <th class="px-4 py-3 text-center text-xs font-semibold text-gray-600 uppercase tracking-wider">
              Acciones
            </th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-100">
          <tr v-for="backup in backups" :key="backup.filename"
              class="hover:bg-gray-50 transition-colors">
            <td class="px-4 py-3">
              <span class="text-sm font-mono text-gray-800">{{ backup.filename }}</span>
            </td>
            <td class="px-4 py-3">
              <span class="text-sm text-gray-600">{{ formatDate(backup.created_at) }}</span>
            </td>
            <td class="px-4 py-3 text-right">
              <span class="text-sm text-gray-600">{{ backup.size_mb }} MB</span>
            </td>
            <td class="px-4 py-3">
              <div class="flex items-center justify-center gap-2">
                <!-- Descargar -->
                <button
                  @click="downloadBackup(backup.filename)"
                  class="p-1.5 text-blue-600 hover:bg-blue-50 rounded-md transition-colors"
                  title="Descargar backup"
                >
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                          d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/>
                  </svg>
                </button>
                <!-- Restaurar -->
                <button
                  @click="openRestoreModal(backup)"
                  class="p-1.5 text-amber-600 hover:bg-amber-50 rounded-md transition-colors"
                  title="Restaurar desde este backup"
                >
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                          d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11
                             11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
                  </svg>
                </button>
                <!-- Eliminar -->
                <button
                  @click="openDeleteModal(backup)"
                  class="p-1.5 text-red-600 hover:bg-red-50 rounded-md transition-colors"
                  title="Eliminar backup"
                >
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                          d="M19 7l-.867 12.142A2 2 0 0116.138
                             21H7.862a2 2 0 01-1.995-1.858L5 7m5
                             4v6m4-6v6m1-10V4a1 1 0
                             00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
                  </svg>
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>

      <!-- Pie de tabla -->
      <div v-if="backups.length > 0" class="px-4 py-2 bg-gray-50 text-xs text-gray-500 text-right">
        {{ backups.length }} backup{{ backups.length !== 1 ? 's' : '' }} disponible{{ backups.length !== 1 ? 's' : '' }}
      </div>
    </div>

    <!-- Modal de restauración -->
    <div v-if="showRestoreModal"
         class="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div class="bg-white rounded-xl shadow-xl max-w-md w-full mx-4 p-6">
        <div class="flex items-center gap-3 mb-4">
          <div class="p-2 bg-amber-100 rounded-full">
            <svg class="w-6 h-6 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0
                       2.502-1.667 1.732-2.5L13.732 4c-.77-1.333-2.694-1.333-3.464
                       0L3.34 16.5c-.77.833.192 2.5 1.732 2.5z"/>
            </svg>
          </div>
          <h3 class="text-lg font-bold text-gray-800">Confirmar restauración</h3>
        </div>

        <div class="mb-4 space-y-2 text-sm text-gray-600">
          <p>
            Está a punto de restaurar la base de datos desde el backup
            <span class="font-mono font-semibold text-gray-800">{{ selectedBackup?.filename }}</span>.
          </p>
          <p class="text-red-600 font-medium">
            Esta operación reemplazará TODOS los datos actuales de la base de datos
            y no es reversible. Asegúrese de tener un backup del estado actual antes
            de continuar.
          </p>
          <p>
            Escriba <span class="font-mono font-bold">RESTAURAR</span> para confirmar:
          </p>
        </div>

        <input
          v-model="confirmationText"
          type="text"
          placeholder="Escriba RESTAURAR"
          class="w-full px-3 py-2 border border-gray-300 rounded-lg mb-4
                 text-sm font-mono focus:ring-2 focus:ring-amber-500
                 focus:border-amber-500 outline-none"
          @keyup.enter="confirmationText === 'RESTAURAR' && executeRestore()"
        />

        <div class="flex justify-end gap-3">
          <button
            @click="closeRestoreModal"
            class="px-4 py-2 text-sm text-gray-700 bg-gray-100
                   hover:bg-gray-200 rounded-lg transition-colors"
          >
            Cancelar
          </button>
          <button
            @click="executeRestore"
            :disabled="confirmationText !== 'RESTAURAR' || restoring"
            class="px-4 py-2 text-sm text-white bg-amber-600
                   hover:bg-amber-700 rounded-lg transition-colors
                   disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {{ restoring ? 'Restaurando...' : 'Restaurar' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Modal de eliminación -->
    <div v-if="showDeleteModal"
         class="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div class="bg-white rounded-xl shadow-xl max-w-sm w-full mx-4 p-6">
        <h3 class="text-lg font-bold text-gray-800 mb-3">Eliminar backup</h3>
        <p class="text-sm text-gray-600 mb-4">
          ¿Confirma la eliminación de
          <span class="font-mono font-semibold">{{ selectedBackup?.filename }}</span>?
          Esta acción no se puede deshacer.
        </p>
        <div class="flex justify-end gap-3">
          <button
            @click="closeDeleteModal"
            class="px-4 py-2 text-sm text-gray-700 bg-gray-100
                   hover:bg-gray-200 rounded-lg transition-colors"
          >
            Cancelar
          </button>
          <button
            @click="executeDelete"
            :disabled="deleting"
            class="px-4 py-2 text-sm text-white bg-red-600
                   hover:bg-red-700 rounded-lg transition-colors
                   disabled:opacity-50"
          >
            {{ deleting ? 'Eliminando...' : 'Eliminar' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

// ── Estado reactivo ──────────────────────────────────────

const backups = ref([])
const loading = ref(true)
const creating = ref(false)
const restoring = ref(false)
const deleting = ref(false)

const statusMessage = ref('')
const statusType = ref('info')

const showRestoreModal = ref(false)
const showDeleteModal = ref(false)
const selectedBackup = ref(null)
const confirmationText = ref('')

// ── API base ─────────────────────────────────────────────

const API_BASE = '/api/v1/admin/backups'

// ── Cargar lista de backups ──────────────────────────────

async function loadBackups() {
  loading.value = true
  try {
    const { data } = await axios.get(API_BASE)
    backups.value = data.backups || []
  } catch (err) {
    showStatus('Error al cargar la lista de backups', 'error')
  } finally {
    loading.value = false
  }
}

// ── Crear backup manual ──────────────────────────────────

async function createBackup() {
  creating.value = true
  clearStatus()
  try {
    const { data } = await axios.post(API_BASE)
    showStatus(
      `Backup creado: ${data.filename} (${data.size_mb} MB)`,
      'success'
    )
    await loadBackups()
  } catch (err) {
    showStatus(
      err.response?.data?.detail || 'Error al crear el backup',
      'error'
    )
  } finally {
    creating.value = false
  }
}

// ── Descargar backup ─────────────────────────────────────

function downloadBackup(filename) {
  // Abre la descarga en una nueva pestaña con el token de auth
  const token = localStorage.getItem('token')
  const url = `${API_BASE}/${filename}/download`

  axios.get(url, { responseType: 'blob' })
    .then(response => {
      const blob = new Blob([response.data])
      const link = document.createElement('a')
      link.href = URL.createObjectURL(blob)
      link.download = filename
      link.click()
      URL.revokeObjectURL(link.href)
      showStatus(`Descarga iniciada: ${filename}`, 'success')
    })
    .catch(() => {
      showStatus('Error al descargar el backup', 'error')
    })
}

// ── Modal de restauración ────────────────────────────────

function openRestoreModal(backup) {
  selectedBackup.value = backup
  confirmationText.value = ''
  showRestoreModal.value = true
}

function closeRestoreModal() {
  showRestoreModal.value = false
  selectedBackup.value = null
  confirmationText.value = ''
}

async function executeRestore() {
  if (confirmationText.value !== 'RESTAURAR') return
  restoring.value = true
  clearStatus()
  try {
    const { data } = await axios.post(
      `${API_BASE}/${selectedBackup.value.filename}/restore`,
      { confirmation: 'RESTAURAR' }
    )
    showStatus(data.message, 'success')
    closeRestoreModal()
    await loadBackups()
  } catch (err) {
    showStatus(
      err.response?.data?.detail || 'Error durante la restauración',
      'error'
    )
  } finally {
    restoring.value = false
  }
}

// ── Modal de eliminación ─────────────────────────────────

function openDeleteModal(backup) {
  selectedBackup.value = backup
  showDeleteModal.value = true
}

function closeDeleteModal() {
  showDeleteModal.value = false
  selectedBackup.value = null
}

async function executeDelete() {
  deleting.value = true
  clearStatus()
  try {
    const { data } = await axios.delete(
      `${API_BASE}/${selectedBackup.value.filename}`
    )
    showStatus(data.message, 'success')
    closeDeleteModal()
    await loadBackups()
  } catch (err) {
    showStatus(
      err.response?.data?.detail || 'Error al eliminar el backup',
      'error'
    )
  } finally {
    deleting.value = false
  }
}

// ── Utilidades ───────────────────────────────────────────

function formatDate(isoString) {
  const d = new Date(isoString)
  return d.toLocaleString('es-ES', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
}

function showStatus(message, type = 'info') {
  statusMessage.value = message
  statusType.value = type
  if (type === 'success') {
    setTimeout(clearStatus, 8000)
  }
}

function clearStatus() {
  statusMessage.value = ''
}

// ── Inicialización ───────────────────────────────────────

onMounted(loadBackups)
</script>
VUEEOF
echo "  → frontend/src/views/admin/BackupsView.vue"

# ────────────────────────────────────────────────────────────
# 7. MODIFICACIÓN DE docker-compose.yml (Python)
# ────────────────────────────────────────────────────────────
echo ""
echo "[7/9] Modificando docker-compose.yml..."

python3 << 'PYMOD'
"""
Modificación de docker-compose.yml para el módulo M8b.
Añade:
  - Volumen backups-dev al servicio db y al servicio backend
  - Mounts de los scripts de backup en el servicio db
  - Entrypoint wrapper en el servicio db (cron de backup)
  - Mount del script de entrypoint del backend (postgresql-client)
  - Declaración del volumen backups-dev en la sección volumes
"""

import sys

COMPOSE_FILE = "docker-compose.yml"

with open(COMPOSE_FILE, "r") as f:
    content = f.read()

changes = []

# ── 1. Añadir volumen backups-dev a la sección volumes ────
# Buscar la sección 'volumes:' de nivel superior y añadir backups-dev
if "backups-dev" not in content:
    # Buscar la última línea de la sección volumes (nivel superior)
    lines = content.split("\n")
    new_lines = []
    in_top_volumes = False
    volume_added = False
    indent_volumes = ""

    for i, line in enumerate(lines):
        new_lines.append(line)

        # Detectar la sección volumes de nivel superior
        stripped = line.strip()
        if stripped == "volumes:" and not line.startswith(" "):
            in_top_volumes = True
            continue

        if in_top_volumes and not volume_added:
            # Detectar el indent usado en las líneas de volumen
            if stripped and not stripped.startswith("#"):
                indent_volumes = line[:len(line) - len(line.lstrip())]
                # Añadir backups-dev justo después de la última declaración
                # Buscamos el final de esta sección
            if stripped == "" or (stripped and not line.startswith(" ") and stripped != "volumes:"):
                # Fin de la sección volumes, insertar antes
                if indent_volumes:
                    new_lines.insert(-1, f"{indent_volumes}backups-dev:")
                else:
                    new_lines.insert(-1, "  backups-dev:")
                volume_added = True
                in_top_volumes = False

    # Si llegamos al final sin añadir
    if not volume_added and in_top_volumes:
        new_lines.append(f"  backups-dev:")
        volume_added = True

    # Si no hay sección volumes, añadirla al final
    if not volume_added:
        new_lines.append("")
        new_lines.append("volumes:")
        # Añadir los volúmenes existentes referenciados y el nuevo
        new_lines.append("  backups-dev:")

    content = "\n".join(new_lines)
    changes.append("Volumen backups-dev declarado en sección volumes")

# ── 2. Añadir mounts y entrypoint al servicio db ─────────
# Buscar el servicio db y añadir los volumes y entrypoint
lines = content.split("\n")
new_lines = []
in_db_service = False
in_db_volumes = False
db_indent = ""
db_volumes_indent = ""
db_volumes_added = False
db_entrypoint_added = False

i = 0
while i < len(lines):
    line = lines[i]
    stripped = line.strip()

    # Detectar inicio del servicio db (puede ser 'db:' o 'cashflow-dev-db:' bajo services)
    if not in_db_service:
        # Buscar la definición del servicio db
        if (stripped.startswith("db:") or stripped.startswith("cashflow-dev-db:")) and "services" not in stripped:
            # Verificar que estamos dentro de services (indent > 0)
            if line.startswith("  ") or line.startswith("\t"):
                in_db_service = True
                db_indent = line[:len(line) - len(line.lstrip())]
        new_lines.append(line)
        i += 1
        continue

    if in_db_service:
        current_indent = line[:len(line) - len(line.lstrip())] if stripped else ""

        # Detectar fin del servicio db (otra clave al mismo nivel)
        if stripped and current_indent and len(current_indent) <= len(db_indent) and stripped.endswith(":"):
            # Antes de salir, añadir lo que falte
            if not db_entrypoint_added and "entrypoint" not in content.split("db:")[1].split("\n")[0:30].__str__():
                child_indent = db_indent + "  "
                new_lines.append(f"{child_indent}entrypoint: ['/usr/local/bin/db_entrypoint.sh']")
                new_lines.append(f"{child_indent}command: ['postgres']")
                db_entrypoint_added = True
            in_db_service = False
            new_lines.append(line)
            i += 1
            continue

        # Detectar sección volumes del servicio db
        if stripped == "volumes:":
            in_db_volumes = True
            db_volumes_indent = current_indent + "  "
            new_lines.append(line)
            i += 1

            # Añadir los volumes al final de la lista existente
            # Primero, copiar los volumes existentes
            while i < len(lines):
                vline = lines[i]
                vstripped = vline.strip()
                if vstripped.startswith("- "):
                    new_lines.append(vline)
                    i += 1
                else:
                    break

            # Añadir los nuevos volumes si no están ya
            if "backups-dev:/backups" not in content:
                new_lines.append(f"{db_volumes_indent}- backups-dev:/backups")
                changes.append("Volume backups-dev:/backups añadido al servicio db")

            if "backup_db.sh" not in content:
                new_lines.append(f"{db_volumes_indent}- ./scripts/backup_db.sh:/usr/local/bin/backup_db.sh")
                changes.append("Mount backup_db.sh añadido al servicio db")

            if "db_entrypoint.sh" not in content:
                new_lines.append(f"{db_volumes_indent}- ./scripts/db_entrypoint.sh:/usr/local/bin/db_entrypoint.sh")
                changes.append("Mount db_entrypoint.sh añadido al servicio db")

            db_volumes_added = True
            in_db_volumes = False
            continue

        new_lines.append(line)
        i += 1
        continue

    new_lines.append(line)
    i += 1

content = "\n".join(new_lines)

# ── 3. Añadir mounts al servicio backend ──────────────────
lines = content.split("\n")
new_lines = []
in_backend = False
backend_indent = ""

i = 0
while i < len(lines):
    line = lines[i]
    stripped = line.strip()

    if not in_backend:
        if stripped.startswith("backend:") and line.startswith("  "):
            in_backend = True
            backend_indent = line[:len(line) - len(line.lstrip())]
        new_lines.append(line)
        i += 1
        continue

    if in_backend:
        current_indent = line[:len(line) - len(line.lstrip())] if stripped else ""

        # Fin del servicio backend
        if stripped and current_indent and len(current_indent) <= len(backend_indent) and stripped.endswith(":"):
            in_backend = False
            new_lines.append(line)
            i += 1
            continue

        # Buscar sección volumes del backend
        if stripped == "volumes:":
            new_lines.append(line)
            i += 1
            vol_indent = current_indent + "  "

            # Copiar volumes existentes
            while i < len(lines):
                vline = lines[i]
                vstripped = vline.strip()
                if vstripped.startswith("- "):
                    new_lines.append(vline)
                    i += 1
                else:
                    break

            # Añadir nuevos volumes del backend
            if "backups-dev:/backups" not in "\n".join(new_lines[-10:]):
                new_lines.append(f"{vol_indent}- backups-dev:/backups")
                changes.append("Volume backups-dev:/backups añadido al servicio backend")

            if "backend_entrypoint.sh" not in content:
                new_lines.append(f"{vol_indent}- ./scripts/backend_entrypoint.sh:/usr/local/bin/backend_entrypoint.sh")
                changes.append("Mount backend_entrypoint.sh añadido al servicio backend")

            continue

        new_lines.append(line)
        i += 1
        continue

    new_lines.append(line)
    i += 1

content = "\n".join(new_lines)

# Escribir resultado
with open(COMPOSE_FILE, "w") as f:
    f.write(content)

for c in changes:
    print(f"  → {c}")

if not changes:
    print("  → Sin cambios necesarios (ya configurado)")
PYMOD

# ────────────────────────────────────────────────────────────
# 8. REGISTRO DEL ROUTER EN main.py (Python)
# ────────────────────────────────────────────────────────────
echo ""
echo "[8/9] Registrando router y middleware en main.py..."

python3 << 'PYMOD'
"""
Registro del router admin_backups y el middleware de mantenimiento
en el fichero principal de la aplicación FastAPI.
"""

MAIN_FILE = "backend/app/main.py"

with open(MAIN_FILE, "r") as f:
    content = f.read()

changes = []

# ── Añadir import del router ──────────────────────────────
if "admin_backups" not in content:
    # Buscar la última línea de imports de routers
    import_line = "from app.routers import admin_backups"

    # Insertar después del último import de routers
    lines = content.split("\n")
    insert_idx = 0
    for idx, line in enumerate(lines):
        if "from app.routers" in line or "from app.routers." in line:
            insert_idx = idx + 1

    if insert_idx == 0:
        # No hay imports de routers, buscar después de los imports generales
        for idx, line in enumerate(lines):
            if line.startswith("from ") or line.startswith("import "):
                insert_idx = idx + 1

    lines.insert(insert_idx, import_line)
    content = "\n".join(lines)
    changes.append("Import de admin_backups añadido")

# ── Añadir import del middleware ──────────────────────────
if "MaintenanceMiddleware" not in content:
    middleware_import = "from app.middleware.maintenance import MaintenanceMiddleware"
    lines = content.split("\n")
    # Insertar después de los otros imports
    insert_idx = 0
    for idx, line in enumerate(lines):
        if line.startswith("from ") or line.startswith("import "):
            insert_idx = idx + 1
    lines.insert(insert_idx, middleware_import)
    content = "\n".join(lines)
    changes.append("Import de MaintenanceMiddleware añadido")

# ── Registrar el router ──────────────────────────────────
if 'admin_backups.router' not in content:
    # Buscar la última llamada a app.include_router
    lines = content.split("\n")
    insert_idx = 0
    for idx, line in enumerate(lines):
        if "app.include_router" in line:
            insert_idx = idx + 1

    if insert_idx > 0:
        # Usar el mismo patrón de registro que los otros routers
        lines.insert(insert_idx, 'app.include_router(admin_backups.router, prefix="/api/v1")')
        content = "\n".join(lines)
        changes.append("Router admin_backups registrado en la aplicación")

# ── Registrar el middleware ───────────────────────────────
if 'MaintenanceMiddleware' not in content or 'add_middleware' not in content:
    # Buscar después de la creación de la app
    lines = content.split("\n")
    insert_idx = 0
    for idx, line in enumerate(lines):
        if "FastAPI(" in line or "app = " in line:
            insert_idx = idx + 1
            # Saltar líneas de configuración de la app
            while insert_idx < len(lines) and (
                lines[insert_idx].strip().startswith(")")
                or lines[insert_idx].strip() == ""
            ):
                insert_idx += 1
            break

    if insert_idx > 0 and "add_middleware(MaintenanceMiddleware)" not in content:
        lines.insert(insert_idx, "")
        lines.insert(insert_idx + 1, "# Middleware de modo mantenimiento (M8b — backups)")
        lines.insert(insert_idx + 2, "app.add_middleware(MaintenanceMiddleware)")
        content = "\n".join(lines)
        changes.append("Middleware de mantenimiento registrado")

with open(MAIN_FILE, "w") as f:
    f.write(content)

for c in changes:
    print(f"  → {c}")
PYMOD

# ────────────────────────────────────────────────────────────
# 9. REGISTRO DE LA RUTA EN EL FRONTEND (Python)
# ────────────────────────────────────────────────────────────
echo ""
echo "[9/9] Registrando ruta /admin/backups en el router frontend..."

python3 << 'PYMOD'
"""
Añade la ruta /admin/backups al router de Vue.js.
"""

ROUTER_FILE = "frontend/src/router/index.js"

with open(ROUTER_FILE, "r") as f:
    content = f.read()

if "/admin/backups" not in content:
    # Definir la nueva ruta
    new_route = """
    {
      path: '/admin/backups',
      name: 'admin-backups',
      component: () => import('../views/admin/BackupsView.vue'),
      meta: { requiresAuth: true, roles: ['admin'] }
    },"""

    # Buscar el array de rutas y añadir antes del cierre
    # Buscar la última ruta definida (último '},' antes de ']')
    lines = content.split("\n")
    insert_idx = 0

    # Estrategia: buscar la última línea con 'path:' y su cierre
    for idx in range(len(lines) - 1, -1, -1):
        line = lines[idx].strip()
        if line == "]" or line == "],":
            # Retroceder para encontrar el cierre del último route object
            for j in range(idx - 1, -1, -1):
                if lines[j].strip().endswith("},") or lines[j].strip().endswith("}"):
                    insert_idx = j + 1
                    break
            break

    if insert_idx > 0:
        lines.insert(insert_idx, new_route)
        content = "\n".join(lines)
        print("  → Ruta /admin/backups añadida al router frontend")
    else:
        print("  ⚠ No se encontró el punto de inserción en el router")
        print("    Añada manualmente la ruta al array de rutas:")
        print(new_route)

    with open(ROUTER_FILE, "w") as f:
        f.write(content)
else:
    print("  → Ruta /admin/backups ya existe en el router")
PYMOD

# ────────────────────────────────────────────────────────────
# RESUMEN
# ────────────────────────────────────────────────────────────
echo ""
echo "============================================================"
echo "  M8b — Instalación completada"
echo "============================================================"
echo ""
echo "  Ficheros creados:"
echo "    scripts/backup_db.sh               Backup pg_dump + retención 30 días"
echo "    scripts/db_entrypoint.sh            Wrapper entrypoint DB (cron 02:00)"
echo "    scripts/backend_entrypoint.sh       Wrapper entrypoint backend (pg_dump)"
echo "    backend/app/services/backup_service.py     Servicio de backups"
echo "    backend/app/middleware/maintenance.py       Middleware modo mantenimiento"
echo "    backend/app/routers/admin_backups.py        Router API (/admin/backups)"
echo "    frontend/src/views/admin/BackupsView.vue   Vista de administración"
echo ""
echo "  Ficheros modificados:"
echo "    docker-compose.yml        Volumen backups-dev, mounts, entrypoints"
echo "    backend/app/main.py       Router + middleware registrados"
echo "    frontend/src/router/index.js   Ruta /admin/backups"
echo ""
echo "  Pasos siguientes:"
echo "    1. Revisar los cambios en docker-compose.yml"
echo "    2. Reconstruir los contenedores:"
echo "       docker compose down"
echo "       docker compose up -d --build --no-cache"
echo "    3. Verificar que el cron está activo en el contenedor db:"
echo "       docker compose exec db crontab -l"
echo "    4. Acceder al panel en https://localhost/admin/backups"
echo "    5. Crear un backup manual de prueba"
echo "    6. Verificar que la descarga funciona"
echo "    7. Probar la restauración (se recomienda crear un"
echo "       backup manual justo antes de probar)"
echo ""
echo "  Endpoints disponibles:"
echo "    GET    /api/v1/admin/backups                     Lista backups"
echo "    POST   /api/v1/admin/backups                     Backup manual"
echo "    GET    /api/v1/admin/backups/{file}/download      Descarga"
echo "    POST   /api/v1/admin/backups/{file}/restore       Restaurar"
echo "    DELETE /api/v1/admin/backups/{file}               Eliminar"
echo ""
echo "  Cron automático: 02:00 diario dentro del contenedor db"
echo "  Retención: 30 días (limpieza automática en cada ejecución)"
echo "============================================================"
