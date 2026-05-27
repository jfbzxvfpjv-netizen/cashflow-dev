-- ════════════════════════════════════════════════════════════════════════════
-- M10b — Nóminas: tablas payroll_periods + payroll_entries
-- Aplicado en dev 27/05/2026. Pendiente aplicar en producción.
-- ════════════════════════════════════════════════════════════════════════════
BEGIN;

CREATE TABLE IF NOT EXISTS payroll_periods (
    id          SERIAL PRIMARY KEY,
    year        SMALLINT NOT NULL,
    month       SMALLINT NOT NULL,
    delegacion  VARCHAR(10) NOT NULL,
    status      VARCHAR(20) NOT NULL DEFAULT 'draft',
    created_by  INTEGER NOT NULL REFERENCES users(id),
    created_at  TIMESTAMP DEFAULT now(),
    paid_at     TIMESTAMP,
    notes       TEXT,
    CONSTRAINT ck_payroll_month     CHECK (month BETWEEN 1 AND 12),
    CONSTRAINT ck_payroll_status    CHECK (status IN ('draft','paid')),
    CONSTRAINT ck_payroll_deleg     CHECK (delegacion IN ('Bata','Malabo')),
    CONSTRAINT uq_payroll_year_month_deleg UNIQUE (year, month, delegacion)
);

CREATE TABLE IF NOT EXISTS payroll_entries (
    id              SERIAL PRIMARY KEY,
    period_id       INTEGER NOT NULL REFERENCES payroll_periods(id) ON DELETE CASCADE,
    employee_id     INTEGER NOT NULL REFERENCES employees(id),
    salary_gross    NUMERIC(12,2) NOT NULL,
    salary_transfer NUMERIC(12,2) NOT NULL,
    cash_amount     NUMERIC(12,2) NOT NULL,
    transaction_id  INTEGER REFERENCES transactions(id),
    paid_at         TIMESTAMP,
    notes           TEXT,
    CONSTRAINT uq_payroll_entry_period_employee UNIQUE (period_id, employee_id),
    CONSTRAINT ck_payroll_entry_amounts CHECK (cash_amount >= 0)
);

CREATE INDEX IF NOT EXISTS idx_payroll_entries_period ON payroll_entries(period_id);
CREATE INDEX IF NOT EXISTS idx_payroll_entries_employee ON payroll_entries(employee_id);
CREATE INDEX IF NOT EXISTS idx_payroll_periods_status ON payroll_periods(status);

COMMIT;
