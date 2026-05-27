# Pliego M10b-v2 - Deducciones automaticas en nomina

Estado: pendiente proxima sesion
Origen: pregunta de Pedro 27/05/2026
Sesion estimada: 1.5 a 2 horas

## 1. Problema

El calculo actual en payroll_service.generate_period es:
cash_amount = max(salary_gross - salary_transfer, 0)

NO descuenta anticipos M9, ni cuotas de prestamos otorgados, ni
retenciones pendientes del empleado. La decision D3 original asumio
"sin deducciones automaticas" pero es fragil: obliga a recordarlo todo
manualmente al editar la entry.

## 2. Saldos del sistema a descontar

- advances: anticipos M9 no liquidados
- installments asociados a Prestamos_Otorgados (cat 48): cuotas pendientes
- retentions: retenciones pendientes contra el empleado

## 3. Plan tecnico

Backend: refactor del bucle en generate_period para calcular
deducciones por empleado y restarlas del cash_amount. Ampliar
payroll_entries con columnas deduction_advances, deduction_loans,
deduction_retentions y manual_override.

Frontend PayrollPeriodDetailView: mostrar desglose por linea en la
tabla y en el modal de pago.

Liquidacion automatica al pagar: marcar settled/paid/released los
registros descontados, transaccional con la creacion de la
transaction de nomina.

Edicion admin: si admin edita cash_amount manualmente, marcar
manual_override=true y NO liquidar automaticamente.

## 4. Decisiones a confirmar antes de empezar

- Deducir saldo TOTAL pendiente o solo cuota del mes
  Recomendado: cuota del mes natural del periodo
- Liquidacion automatica al pagar o manual
  Recomendado: automatica
- Caso deudor neto cash_amount = 0
  Recomendado: entry se crea con 0, deducciones del mes SI se aplican

## 5. Migracion

ALTER TABLE payroll_entries
  ADD COLUMN deduction_advances NUMERIC default 0,
  ADD COLUMN deduction_loans NUMERIC default 0,
  ADD COLUMN deduction_retentions NUMERIC default 0,
  ADD COLUMN manual_override BOOLEAN default FALSE;

## 6. Fuera de alcance

- IRPF o retenciones fiscales
- Anticipos en moneda distinta a XAF
- Liquidacion de saldos disputados
