-- Permite override del counterparty_type a nivel de subcategoría
-- Caso de uso: Transporte (supplier) pero Taxi dentro (employee)
BEGIN;
ALTER TABLE transaction_subcategories
  ADD COLUMN IF NOT EXISTS counterparty_type VARCHAR(20)
  CHECK (counterparty_type IN ('employee','supplier','partner','external','any','none'));

-- Aplicar override: Taxi → employee
UPDATE transaction_subcategories
SET counterparty_type='employee'
WHERE id=129 AND name='Taxi';

COMMIT;

SELECT tc.name AS categoria, tc.counterparty_type AS cat_type,
       ts.name AS subcategoria, ts.counterparty_type AS sub_type,
       COALESCE(ts.counterparty_type, tc.counterparty_type) AS efectivo
FROM transaction_subcategories ts
JOIN transaction_categories tc ON ts.category_id=tc.id
WHERE tc.name='Transporte'
ORDER BY ts.id;

-- Sesion posterior 01/06/2026: Peajes tambien es reembolso a empleado
UPDATE transaction_subcategories SET counterparty_type='employee' WHERE id=128 AND name='Peajes';
