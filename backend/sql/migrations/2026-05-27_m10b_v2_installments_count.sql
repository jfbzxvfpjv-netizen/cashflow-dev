BEGIN;

ALTER TABLE advances_loans
  ADD COLUMN IF NOT EXISTS installments_count INTEGER;

-- Primero poblar los prestamos existentes
UPDATE advances_loans SET installments_count = 4 WHERE id = 1 AND type = 'loan';
UPDATE advances_loans SET installments_count = 1 WHERE type = 'loan' AND installments_count IS NULL;

-- Ahora si agregar el constraint con datos validos
ALTER TABLE advances_loans
  DROP CONSTRAINT IF EXISTS ck_loan_installments_count;
ALTER TABLE advances_loans
  ADD CONSTRAINT ck_loan_installments_count
    CHECK (
      (type = 'advance' AND installments_count IS NULL) OR
      (type = 'loan' AND installments_count IS NOT NULL AND installments_count >= 1)
    );

COMMIT;
