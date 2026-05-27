-- ════════════════════════════════════════════════════════════════════════════
-- M10a fix 27/05/2026: ampliar approval_status de VARCHAR(15) a VARCHAR(20)
-- Razón: el valor 'pending_approval' tiene 16 caracteres y no cabía en VARCHAR(15),
-- haciendo fallar cualquier transacción que superase un umbral configurado.
-- Aplicado en dev y producción durante la sesión M10a.
-- ════════════════════════════════════════════════════════════════════════════
ALTER TABLE transactions ALTER COLUMN approval_status TYPE VARCHAR(20);
