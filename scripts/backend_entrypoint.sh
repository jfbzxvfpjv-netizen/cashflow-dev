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
