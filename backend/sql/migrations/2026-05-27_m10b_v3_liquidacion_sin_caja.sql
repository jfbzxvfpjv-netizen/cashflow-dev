-- M10b-v3: liquidacion sin movimiento de caja
-- Aplicar en payroll_entries para empleados deudor neto crónico
BEGIN;

ALTER TABLE payroll_entries
  ADD COLUMN IF NOT EXISTS liquidated_without_cash BOOLEAN NOT NULL DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS liquidated_at TIMESTAMP,
  ADD COLUMN IF NOT EXISTS liquidated_by INTEGER REFERENCES users(id);

COMMIT;

SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name='payroll_entries'
  AND column_name IN ('liquidated_without_cash','liquidated_at','liquidated_by');
