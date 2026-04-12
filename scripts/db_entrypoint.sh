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
