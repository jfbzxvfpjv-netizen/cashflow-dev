# Pliego M10b — Nóminas (Payroll) — v1

**Fecha**: 27/05/2026
**Estado**: diseño cerrado, en implementación

## Alcance

Procesar nóminas mensuales para empleados de R2i Network. Cada mes natural,
para cada delegación (Bata/Malabo), se genera un periodo con N entradas (una
por empleado activo). Cada entrada arrastra el `salary_gross` y `salary_transfer`
del empleado en el momento de generación (snapshot inmutable). El importe a
pagar en caja es `cash_amount = salary_gross - salary_transfer` (la diferencia
hasta el bruto se paga por transferencia bancaria, fuera de Caja R2i).

Cuando el gestor lanza los pagos, cada entrada genera una transacción de gasto
individual (categoría Nominas_Personal, subcat Salarios, proyecto General,
obra Administracion). Cada transacción pasa por el hook M10a — si supera el
umbral configurado, queda en `pending_approval` hasta que el admin la apruebe.

## Decisiones cerradas (27/05)

- D1: solo se paga por caja `salary_gross - salary_transfer`
- D2: periodo siempre mes natural (1-último día)
- D3: sin deducciones automáticas (operador ajusta manualmente)
- D4: N transacciones individuales (una por empleado), no operación contenedora
- D5: umbral M10a aplica por empleado individual (vía hook estándar de
  `financial_helpers.create_transaction`)

## Modelo de datos

### `payroll_periods`
- id (PK), year (SMALLINT), month (1-12), delegacion (Bata/Malabo)
- status: 'draft' | 'paid'
- created_by/at, paid_at, notes
- UNIQUE (year, month, delegacion)

### `payroll_entries`
- id (PK), period_id (FK CASCADE), employee_id (FK)
- salary_gross / salary_transfer (snapshot al generar)
- cash_amount (= gross - transfer al generar, editable manualmente)
- transaction_id (FK, NULL hasta lanzar pago), paid_at, notes
- UNIQUE (period_id, employee_id)

## Flujo operativo

1. **Admin genera periodo** (mes/año/delegación) → crea PayrollPeriod en 'draft'
   + N PayrollEntries (uno por empleado activo de esa delegación).
2. **Admin edita** cash_amount de entradas individuales si hace falta (bonos,
   descuentos, ausencias).
3. **Gestor lanza pagos**: para cada entry con `cash_amount > 0` y sin
   transaction_id, crea Transaction vía `financial_helpers.create_transaction()`.
   Si supera umbral M10a → pending_approval. Marca entry.transaction_id.
4. **Admin cierra periodo** cuando todas las entries con cash_amount > 0 ya
   tienen transaction_id (status='paid', paid_at = now).

## Categorías y catálogos usados

- Categoría: 29 (Nominas_Personal)
- Subcategoría: 100 (Salarios)
- Proyecto: 18 (General), Obra: 107 (Administracion)

## NO incluido en v1 (futuro)

- Deducciones automáticas (INSESO, IGI, otros)
- Reportes complejos (PDF nómina individual, listado masivo)
- Bonificaciones recurrentes configurables
- Histórico de cambios de salario integrado (la tabla `employee_salary_history`
  ya existe pero no se usa explícitamente; el snapshot del entry sustituye)

