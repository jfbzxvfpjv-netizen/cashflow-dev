-- ════════════════════════════════════════════════════════════════════════════
-- Consolidación 27/05/2026: M11 (huellas + firma multi-método) + H2 (4 pasos)
-- Aplicar en BD producción cashflow.
-- Idempotente: usa IF NOT EXISTS y bloques DO con verificación de existencia.
-- ════════════════════════════════════════════════════════════════════════════
BEGIN;

-- ── M11 huellas: tabla nueva ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS employee_fingerprints (
    id              SERIAL PRIMARY KEY,
    employee_id     INTEGER NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    finger_position VARCHAR(20) NOT NULL,
    capture_index   SMALLINT NOT NULL,
    template_bytes  BYTEA NOT NULL,
    quality_score   SMALLINT,
    created_at      TIMESTAMP DEFAULT now(),
    created_by      INTEGER NOT NULL REFERENCES users(id),
    CONSTRAINT employee_fingerprints_capture_index_check CHECK (capture_index >= 1 AND capture_index <= 4),
    CONSTRAINT employee_fingerprints_quality_score_check CHECK (quality_score >= 0 AND quality_score <= 100),
    CONSTRAINT employee_fingerprints_finger_position_check CHECK (finger_position IN (
        'right_thumb','right_index','right_middle','right_ring','right_pinky',
        'left_thumb','left_index','left_middle','left_ring','left_pinky'
    )),
    CONSTRAINT employee_fingerprints_employee_id_finger_position_capture_i_key UNIQUE (employee_id, finger_position, capture_index)
);
CREATE INDEX IF NOT EXISTS idx_emp_fingerprints_employee ON employee_fingerprints(employee_id);
CREATE INDEX IF NOT EXISTS idx_emp_fingerprints_lookup ON employee_fingerprints(employee_id, finger_position);

-- ── M11 firmas: columnas nuevas en transaction_signatures ────────────────────
ALTER TABLE transaction_signatures ADD COLUMN IF NOT EXISTS signature_method            VARCHAR(30) NOT NULL DEFAULT 'wacom';
ALTER TABLE transaction_signatures ADD COLUMN IF NOT EXISTS fingerprint_score           SMALLINT;
ALTER TABLE transaction_signatures ADD COLUMN IF NOT EXISTS fingerprint_finger_position VARCHAR(20);
ALTER TABLE transaction_signatures ADD COLUMN IF NOT EXISTS fingerprint_attempts        SMALLINT;
ALTER TABLE transaction_signatures ADD COLUMN IF NOT EXISTS fingerprint_failed_scores   TEXT;
ALTER TABLE transaction_signatures ADD COLUMN IF NOT EXISTS signer_user_id              INTEGER;

-- FK signer_user_id solo si no existe ya
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE table_name='transaction_signatures'
          AND constraint_name='transaction_signatures_signer_user_id_fkey'
    ) THEN
        ALTER TABLE transaction_signatures
            ADD CONSTRAINT transaction_signatures_signer_user_id_fkey
            FOREIGN KEY (signer_user_id) REFERENCES users(id);
    END IF;
END $$;

-- ── H2: bank_withdrawal_requests delta 4 pasos ───────────────────────────────
ALTER TABLE bank_withdrawal_requests ADD COLUMN IF NOT EXISTS requested_by  INTEGER REFERENCES users(id);
ALTER TABLE bank_withdrawal_requests ADD COLUMN IF NOT EXISTS requested_at  TIMESTAMP;
ALTER TABLE bank_withdrawal_requests ADD COLUMN IF NOT EXISTS reason        TEXT;
ALTER TABLE bank_withdrawal_requests ADD COLUMN IF NOT EXISTS formalized_by INTEGER REFERENCES users(id);
ALTER TABLE bank_withdrawal_requests ADD COLUMN IF NOT EXISTS formalized_at TIMESTAMP;

-- Hacer NULLABLE los que solo se conocen tras FORMALIZAR
ALTER TABLE bank_withdrawal_requests ALTER COLUMN cheque_reference     DROP NOT NULL;
ALTER TABLE bank_withdrawal_requests ALTER COLUMN corporate_account_id DROP NOT NULL;

-- Actualizar CHECK constraint a los 5 nuevos estados
ALTER TABLE bank_withdrawal_requests DROP CONSTRAINT IF EXISTS ck_bw_status;
ALTER TABLE bank_withdrawal_requests ADD  CONSTRAINT ck_bw_status
    CHECK (status IN ('requested','formalized','approved','confirmed','rejected'));

COMMIT;
