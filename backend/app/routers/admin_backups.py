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

from fastapi import APIRouter, Depends, HTTPException, status, Request, UploadFile, File, UploadFile, File
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


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_backup(
    request: Request,
    file: UploadFile = File(...),
    current_user=Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """
    Sube un fichero de backup .dump al volumen de backups.
    Solo acepta ficheros con extensión .dump.
    """
    if not file.filename or not file.filename.endswith(".dump"):
        raise HTTPException(status_code=400, detail="Solo se permiten ficheros .dump")

    import re
    if not re.match(r'^[a-zA-Z0-9_\-]+\.dump$', file.filename):
        raise HTTPException(status_code=400, detail="Nombre de fichero no válido")

    import os
    filepath = os.path.join("/backups", file.filename)
    if os.path.exists(filepath):
        raise HTTPException(status_code=409, detail=f"Ya existe un backup con el nombre '{file.filename}'")

    contents = await file.read()
    with open(filepath, "wb") as f:
        f.write(contents)

    stat = os.stat(filepath)
    _audit_log(
        db,
        user_id=current_user.id,
        action="BACKUP_UPLOADED",
        details={"filename": file.filename, "size_mb": round(stat.st_size / (1024 * 1024), 2)},
        ip_address=_get_client_ip(request),
    )

    return {
        "message": f"Backup '{file.filename}' subido correctamente",
        "filename": file.filename,
        "size_bytes": stat.st_size,
        "size_mb": round(stat.st_size / (1024 * 1024), 2),
    }
