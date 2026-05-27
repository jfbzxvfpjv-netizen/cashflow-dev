"""
M10b-v2: Helper para calcular deducciones automaticas de nomina.

Reglas (confirmadas con Pedro 27/05/2026):
- Anticipo (advances_loans type=advance, status open/partial): saldo total
  pendiente del empleado se descuenta en una sola nomina
- Prestamo (advances_loans type=loan,    status open/partial): cuota mensual
  = amount / installments_count, limitada al saldo pendiente
- Retencion (retentions_deposits status=pending, employee): solo si
  release_date cae en el mes del periodo, descontar amount completo
- Installment_payments NO aplica (solo para proveedores, no a empleados)
"""
from decimal import Decimal
from datetime import date
from calendar import monthrange
from sqlalchemy import text
from sqlalchemy.orm import Session


def calculate_deductions(db: Session, employee_id: int, year: int, month: int) -> dict:
    """
    Calcula deducciones automaticas a aplicar a la nomina del empleado en el
    mes indicado. Devuelve dict con totales, IDs y desglose por linea para
    poder mostrar al admin y liquidar automaticamente al pagar.
    """
    refs = {
        'advances': [],     # {advance_id, amount_to_deduct}
        'loans': [],        # {loan_id, amount_to_deduct (cuota), total, installments}
        'retentions': [],   # {retention_id, amount}
    }

    # 1. Anticipos (descuento total del saldo pendiente)
    advances_total = Decimal(0)
    rows = db.execute(text("""
        SELECT id, (amount - amount_repaid) AS saldo
        FROM advances_loans
        WHERE employee_id = :eid
          AND type = 'advance'
          AND status IN ('open', 'partial')
          AND (amount - amount_repaid) > 0
        ORDER BY opened_at
    """), {'eid': employee_id}).fetchall()
    for r in rows:
        saldo = Decimal(r.saldo)
        advances_total += saldo
        refs['advances'].append({'advance_id': r.id, 'amount': str(saldo)})

    # 2. Prestamos (cuota mensual = amount / installments_count)
    loans_total = Decimal(0)
    rows = db.execute(text("""
        SELECT id, amount, installments_count, (amount - amount_repaid) AS saldo
        FROM advances_loans
        WHERE employee_id = :eid
          AND type = 'loan'
          AND status IN ('open', 'partial')
          AND (amount - amount_repaid) > 0
        ORDER BY opened_at
    """), {'eid': employee_id}).fetchall()
    for r in rows:
        amount = Decimal(r.amount)
        count = max(r.installments_count or 1, 1)
        saldo = Decimal(r.saldo)
        cuota = (amount / count).quantize(Decimal('0.01'))
        # No descontar mas del saldo pendiente (ultima cuota suele ser ajustada)
        cuota = min(cuota, saldo)
        if cuota > 0:
            loans_total += cuota
            refs['loans'].append({
                'loan_id': r.id,
                'amount': str(cuota),
                'total': str(amount),
                'installments': count,
                'remaining_saldo': str(saldo),
            })

    # 3. Retenciones que vencen en el mes del periodo
    last_day = date(year, month, monthrange(year, month)[1])
    first_day = date(year, month, 1)
    retentions_total = Decimal(0)
    rows = db.execute(text("""
        SELECT id, amount
        FROM retentions_deposits
        WHERE employee_id = :eid
          AND status = 'pending'
          AND release_date IS NOT NULL
          AND release_date BETWEEN :fd AND :ld
    """), {'eid': employee_id, 'fd': first_day, 'ld': last_day}).fetchall()
    for r in rows:
        retentions_total += Decimal(r.amount)
        refs['retentions'].append({'retention_id': r.id, 'amount': str(Decimal(r.amount))})

    total = advances_total + loans_total + retentions_total
    return {
        'advances': advances_total,
        'loans': loans_total,
        'retentions': retentions_total,
        'total': total,
        'refs': refs,
    }
