# Pliego M10b-v3: Liquidación de deducciones sin movimiento de caja

## Problema
Empleados con cuotas mensuales > bruto disponible (caso Adama, Bata):
sus deducciones quedan capadas, pero el saldo de préstamos no avanza
mientras espere a un mes con caja suficiente. Necesidad: poder liquidar
las deducciones aunque no se pague nada en caja.

## Decisión de diseño (Opción A — simple)
- Solo se decrementa `advances_loans.amount_repaid` y se marcan retenciones
  como released. NO se crea `Transaction` en caja.
- Auditoria queda en `payroll_entries.deduction_refs` (ya existe) + nuevas
  columnas marcando la liquidación sin caja.
- La caja sigue reflejando la realidad: no hay movimiento porque no hay dinero.

## Cambios BD
ALTER TABLE payroll_entries
  ADD COLUMN liquidated_without_cash BOOLEAN NOT NULL DEFAULT FALSE,
  ADD COLUMN liquidated_at TIMESTAMP,
  ADD COLUMN liquidated_by INTEGER REFERENCES users(id);

## Backend
- Nuevo método `payroll_service.liquidate_without_cash(entry_id, signature_payload, user)`:
  - Validaciones: periodo draft, entry sin pagar, gestor de la delegación,
    cash_amount=0 estrictamente (si hay caja a pagar, debe usar 'Pagar' normal)
  - Aplica `repay_by_payroll` por cada advance/loan en deduction_refs
  - Marca retenciones como released
  - Marca entry.liquidated_without_cash=true, liquidated_at=now, liquidated_by=user
  - Audit log

- Endpoint: `PUT /payrolls/{period_id}/entries/{entry_id}/liquidate-no-cash`

## Frontend
- En PayrollPeriodDetailView, cuando `entry.cash_amount === 0` Y hay
  deducciones (`totalDeductions(entry) > 0`):
  - Mostrar botón "Liquidar sin caja" (en lugar del actual mensaje "Sin efectivo")
  - Modal de confirmación con desglose y firma del empleado obligatoria
- Tras liquidación: entry queda con `liquidated_without_cash=true`, sin transaction_id
  pero con indicador visible "Liquidado sin caja"

## Firma
Sigue siendo obligatoria: el empleado firma que acepta el descuento de sus
préstamos aunque no reciba caja. Misma SignatureSection con contraparte=employee.

## Restricciones
- Si cash_amount > 0: usar flujo de pago normal (no esta opción)
- Si periodo cerrado: no permitido
- Si entry ya pagada o liquidada: no permitido
- Solo gestor de la delegación
