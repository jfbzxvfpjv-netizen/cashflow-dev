-- ════════════════════════════════════════════════════════════════════════════
-- M14 — Normalización de entrada de datos por categoría (27/05/2026)
-- Añade reglas de obligatoriedad de contraparte y vehículo por categoría
-- ════════════════════════════════════════════════════════════════════════════
BEGIN;

ALTER TABLE transaction_categories
  ADD COLUMN IF NOT EXISTS counterparty_type VARCHAR(20) NOT NULL DEFAULT 'external',
  ADD COLUMN IF NOT EXISTS requires_vehicle BOOLEAN NOT NULL DEFAULT FALSE;

ALTER TABLE transaction_categories DROP CONSTRAINT IF EXISTS ck_counterparty_type;
ALTER TABLE transaction_categories ADD CONSTRAINT ck_counterparty_type
  CHECK (counterparty_type IN ('employee','supplier','partner','external','any','none'));

-- Mapeo inicial (refinable con uso diario)
UPDATE transaction_categories SET counterparty_type='employee' WHERE id IN (34, 37, 49, 45, 29, 48);
UPDATE transaction_categories SET counterparty_type='supplier' WHERE id IN (41, 30, 35, 42, 33, 39, 32, 40, 36, 31, 38, 53);
UPDATE transaction_categories SET counterparty_type='partner'  WHERE id = 46;
UPDATE transaction_categories SET counterparty_type='external' WHERE id IN (44, 51);
UPDATE transaction_categories SET counterparty_type='any'      WHERE id IN (54, 43);
UPDATE transaction_categories SET counterparty_type='none'     WHERE id IN (50, 55, 47, 52);
UPDATE transaction_categories SET requires_vehicle=TRUE        WHERE id = 31;

COMMIT;
