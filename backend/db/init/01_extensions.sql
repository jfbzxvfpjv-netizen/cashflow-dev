-- ============================================================================
-- Inicialización de PostgreSQL — extensiones requeridas
-- ============================================================================
-- Este script se ejecuta automáticamente al crear la base de datos por primera
-- vez gracias al montaje en /docker-entrypoint-initdb.d.
-- ============================================================================

-- Extensión pgcrypto para cifrado de campos sensibles (salarios, saldos de socios)
CREATE EXTENSION IF NOT EXISTS pgcrypto;
