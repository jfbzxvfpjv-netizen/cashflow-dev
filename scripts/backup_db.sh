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
