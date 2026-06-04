-- Decision operativa 04/06/2026: flexibilizar todas las reglas M14.
-- Todas las categorias activas pasan a counterparty_type='any' y se
-- eliminan los overrides de subcategoria (Taxi, Peajes, Envio_Aereo),
-- ahora redundantes.
--
-- Implicacion: el sistema acepta cualquier contraparte (catalogo o
-- texto libre) en cualquier categoria, salvo que se restablezcan
-- reglas estrictas en el futuro.
BEGIN;
UPDATE transaction_categories SET counterparty_type='any' WHERE active=TRUE;
UPDATE transaction_subcategories SET counterparty_type=NULL WHERE counterparty_type IS NOT NULL;
COMMIT;
