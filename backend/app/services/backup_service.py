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
