"""
Servicio de Dashboard — M8
Cálculos de saldo actual, indicadores del día, alertas prioritarias,
movimientos por período y datos para gráficos Chart.js.
"""
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Optional, List, Dict, Any

from sqlalchemy import func, case, and_, cast, Date
from sqlalchemy.orm import Session

from app.models.cash_flow import (
    SystemConfig, CashSession, Transaction,
    TransactionProject, BankWithdrawalRequest
)
from app.models.catalogs import (
    TransactionCategory, TransactionSubcategory,
    Supplier, Employee, Partner
)


class DashboardService:
    """Servicio centralizado para todos los cálculos del dashboard."""

    @staticmethod
    def get_saldo_actual(db: Session, delegacion: Optional[str] = None) -> Decimal:
        """
        Calcula el saldo actual de la caja.
        saldo = opening_balance + SUM(ingresos approved) - SUM(egresos approved)
        Solo computan transacciones con approval_status='approved' y cancelled=False.
        """
        if delegacion and delegacion != 'Consolidado':
            config = db.query(SystemConfig).filter(
                SystemConfig.delegacion == delegacion
            ).first()
            opening = config.opening_balance if config else Decimal('0')
            deleg_filter = Transaction.delegacion == delegacion
        else:
            # Consolidado: sumar ambas delegaciones
            configs = db.query(SystemConfig).all()
            opening = sum((c.opening_balance for c in configs), Decimal('0'))
            deleg_filter = True  # Sin filtro de delegación

        base_filter = and_(
            deleg_filter,
            Transaction.approval_status == 'approved',
            Transaction.cancelled == False
        )

        ingresos = db.query(
            func.coalesce(func.sum(Transaction.amount), Decimal('0'))
        ).filter(base_filter, Transaction.type == 'income').scalar()

        egresos = db.query(
            func.coalesce(func.sum(Transaction.amount), Decimal('0'))
        ).filter(base_filter, Transaction.type == 'expense').scalar()

        return opening + ingresos - egresos

    @staticmethod
    def get_indicadores_hoy(db: Session, delegacion: Optional[str] = None) -> Dict[str, Any]:
        """Indicadores del día en curso: ingresos, egresos y número de transacciones."""
        hoy = date.today()
        filters = [
            cast(Transaction.created_at, Date) == hoy,
            Transaction.approval_status == 'approved',
            Transaction.cancelled == False
        ]
        if delegacion and delegacion != 'Consolidado':
            filters.append(Transaction.delegacion == delegacion)

        ingresos_hoy = db.query(
            func.coalesce(func.sum(Transaction.amount), Decimal('0'))
        ).filter(*filters, Transaction.type == 'income').scalar()

        egresos_hoy = db.query(
            func.coalesce(func.sum(Transaction.amount), Decimal('0'))
        ).filter(*filters, Transaction.type == 'expense').scalar()

        count_filters = [
            cast(Transaction.created_at, Date) == hoy,
            Transaction.cancelled == False
        ]
        if delegacion and delegacion != 'Consolidado':
            count_filters.append(Transaction.delegacion == delegacion)

        transacciones_hoy = db.query(
            func.count(Transaction.id)
        ).filter(*count_filters).scalar()

        return {
            "ingresos_hoy": float(ingresos_hoy),
            "egresos_hoy": float(egresos_hoy),
            "transacciones_hoy": transacciones_hoy or 0
        }

    @staticmethod
    def get_alertas(db: Session, delegacion: Optional[str] = None) -> Dict[str, int]:
        """Contadores de alertas prioritarias."""
        deleg_filters_tx = []
        deleg_filters_bw = []
        if delegacion and delegacion != 'Consolidado':
            deleg_filters_tx.append(Transaction.delegacion == delegacion)
            deleg_filters_bw.append(BankWithdrawalRequest.delegacion == delegacion)

        # Transacciones pendientes de aprobación
        pending_approval = db.query(func.count(Transaction.id)).filter(
            Transaction.approval_status == 'pending_approval',
            Transaction.cancelled == False,
            *deleg_filters_tx
        ).scalar() or 0

        # Transacciones autorizadas pendientes de ejecución
        authorized_pending = db.query(func.count(Transaction.id)).filter(
            Transaction.approval_status == 'authorized',
            Transaction.cancelled == False,
            *deleg_filters_tx
        ).scalar() or 0

        # Retiradas bancarias pendientes (pending o approved sin confirmar)
        bank_pending = db.query(func.count(BankWithdrawalRequest.id)).filter(
            BankWithdrawalRequest.status.in_(['pending', 'approved']),
            *deleg_filters_bw
        ).scalar() or 0

        return {
            "pending_approval": pending_approval,
            "authorized_pending": authorized_pending,
            "bank_withdrawals_pending": bank_pending
        }

    @staticmethod
    def get_movimientos(
        db: Session,
        delegacion: Optional[str],
        date_start: Optional[date],
        date_end: Optional[date],
        tipo: Optional[str] = None,
        category_id: Optional[int] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Dict[str, Any]:
        """Lista paginada de movimientos del período con filtros inline."""
        query = db.query(Transaction)

        if delegacion and delegacion != 'Consolidado':
            query = query.filter(Transaction.delegacion == delegacion)
        if date_start:
            query = query.filter(cast(Transaction.created_at, Date) >= date_start)
        if date_end:
            query = query.filter(cast(Transaction.created_at, Date) <= date_end)
        if tipo:
            query = query.filter(Transaction.type == tipo)
        if category_id:
            query = query.filter(Transaction.category_id == category_id)

        total = query.count()
        transactions = query.order_by(Transaction.created_at.desc()).offset(
            (page - 1) * page_size
        ).limit(page_size).all()

        items = []
        for t in transactions:
            # Obtener nombre de categoría
            cat = db.query(TransactionCategory).filter(
                TransactionCategory.id == t.category_id
            ).first()
            subcat = db.query(TransactionSubcategory).filter(
                TransactionSubcategory.id == t.subcategory_id
            ).first()

            # Determinar contraparte
            contraparte = t.counterparty_free or ''
            if t.supplier_id:
                sup = db.query(Supplier).filter(Supplier.id == t.supplier_id).first()
                if sup:
                    contraparte = sup.name
            elif t.employee_id:
                emp = db.query(Employee).filter(Employee.id == t.employee_id).first()
                if emp:
                    contraparte = emp.full_name
            elif t.partner_id:
                par = db.query(Partner).filter(Partner.id == t.partner_id).first()
                if par:
                    contraparte = par.full_name

            # Estado legible
            if t.cancelled:
                estado = 'anulada'
            elif t.approval_status == 'pending_approval':
                estado = 'pendiente'
            elif t.approval_status == 'authorized':
                estado = 'autorizada'
            elif t.approval_status == 'rejected':
                estado = 'rechazada'
            else:
                estado = 'aprobada'

            items.append({
                "id": t.id,
                "fecha": t.created_at.isoformat() if t.created_at else None,
                "referencia": t.reference_number,
                "concepto": t.concept,
                "categoria": cat.name if cat else '',
                "subcategoria": subcat.name if subcat else '',
                "contraparte": contraparte,
                "tipo": t.type,
                "importe": float(t.amount),
                "estado": estado,
                "delegacion": t.delegacion,
                "cancelled": t.cancelled,
                "imported": t.imported
            })

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": (total + page_size - 1) // page_size if page_size > 0 else 0
        }

    @staticmethod
    def get_grafico_evolucion(
        db: Session,
        delegacion: Optional[str],
        date_start: date,
        date_end: date
    ) -> List[Dict[str, Any]]:
        """Datos para el gráfico de evolución del saldo día a día."""
        # Calcular saldo acumulado ANTES del período seleccionado
        filters_pre = [
            cast(Transaction.created_at, Date) < date_start,
            Transaction.approval_status == 'approved',
            Transaction.cancelled == False
        ]
        if delegacion and delegacion != 'Consolidado':
            filters_pre.append(Transaction.delegacion == delegacion)

        if delegacion and delegacion != 'Consolidado':
            config = db.query(SystemConfig).filter(
                SystemConfig.delegacion == delegacion
            ).first()
            opening = float(config.opening_balance) if config else 0.0
        else:
            configs = db.query(SystemConfig).all()
            opening = sum(float(c.opening_balance) for c in configs)

        ingresos_pre = float(db.query(
            func.coalesce(func.sum(Transaction.amount), 0)
        ).filter(*filters_pre, Transaction.type == 'income').scalar())

        egresos_pre = float(db.query(
            func.coalesce(func.sum(Transaction.amount), 0)
        ).filter(*filters_pre, Transaction.type == 'expense').scalar())

        saldo_acum = opening + ingresos_pre - egresos_pre

        # Obtener movimientos diarios en el período
        filters_periodo = [
            cast(Transaction.created_at, Date) >= date_start,
            cast(Transaction.created_at, Date) <= date_end,
            Transaction.approval_status == 'approved',
            Transaction.cancelled == False
        ]
        if delegacion and delegacion != 'Consolidado':
            filters_periodo.append(Transaction.delegacion == delegacion)

        daily = db.query(
            cast(Transaction.created_at, Date).label('fecha'),
            func.coalesce(func.sum(case(
                (Transaction.type == 'income', Transaction.amount),
                else_=0
            )), 0).label('ingresos'),
            func.coalesce(func.sum(case(
                (Transaction.type == 'expense', Transaction.amount),
                else_=0
            )), 0).label('egresos')
        ).filter(*filters_periodo).group_by(
            cast(Transaction.created_at, Date)
        ).order_by(cast(Transaction.created_at, Date)).all()

        # Construir serie temporal completa (incluir días sin movimientos)
        result = []
        current = date_start
        daily_dict = {str(row.fecha): row for row in daily}

        while current <= date_end:
            key = str(current)
            if key in daily_dict:
                row = daily_dict[key]
                saldo_acum += float(row.ingresos) - float(row.egresos)
            result.append({
                "fecha": key,
                "saldo": round(saldo_acum, 2)
            })
            current += timedelta(days=1)

        return result

    @staticmethod
    def get_grafico_ingresos_egresos(
        db: Session,
        delegacion: Optional[str],
        date_start: date,
        date_end: date
    ) -> List[Dict[str, Any]]:
        """Datos para el gráfico de barras agrupadas ingresos vs egresos."""
        dias = (date_end - date_start).days + 1
        # Si el período es mayor a 31 días, agrupar por semana
        agrupar_semanal = dias > 31

        filters = [
            cast(Transaction.created_at, Date) >= date_start,
            cast(Transaction.created_at, Date) <= date_end,
            Transaction.approval_status == 'approved',
            Transaction.cancelled == False
        ]
        if delegacion and delegacion != 'Consolidado':
            filters.append(Transaction.delegacion == delegacion)

        if agrupar_semanal:
            # Agrupar por semana ISO
            week_expr = func.to_char(Transaction.created_at, 'IYYY-IW')
            rows = db.query(
                week_expr.label('periodo'),
                func.coalesce(func.sum(case(
                    (Transaction.type == 'income', Transaction.amount), else_=0
                )), 0).label('ingresos'),
                func.coalesce(func.sum(case(
                    (Transaction.type == 'expense', Transaction.amount), else_=0
                )), 0).label('egresos')
            ).filter(*filters).group_by(week_expr).order_by(week_expr).all()

            return [{
                "fecha": f"Sem {row.periodo}",
                "ingresos": float(row.ingresos),
                "egresos": float(row.egresos)
            } for row in rows]
        else:
            rows = db.query(
                cast(Transaction.created_at, Date).label('fecha'),
                func.coalesce(func.sum(case(
                    (Transaction.type == 'income', Transaction.amount), else_=0
                )), 0).label('ingresos'),
                func.coalesce(func.sum(case(
                    (Transaction.type == 'expense', Transaction.amount), else_=0
                )), 0).label('egresos')
            ).filter(*filters).group_by(
                cast(Transaction.created_at, Date)
            ).order_by(cast(Transaction.created_at, Date)).all()

            return [{
                "fecha": str(row.fecha),
                "ingresos": float(row.ingresos),
                "egresos": float(row.egresos)
            } for row in rows]

    @classmethod
    def get_summary(
        cls,
        db: Session,
        delegacion: Optional[str] = None,
        date_start: Optional[date] = None,
        date_end: Optional[date] = None,
        tipo: Optional[str] = None,
        category_id: Optional[int] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Dict[str, Any]:
        """Devuelve todos los datos del dashboard en una sola llamada."""
        if not date_start:
            date_start = date.today()
        if not date_end:
            date_end = date.today()

        saldo = cls.get_saldo_actual(db, delegacion)
        indicadores = cls.get_indicadores_hoy(db, delegacion)
        alertas = cls.get_alertas(db, delegacion)
        movimientos = cls.get_movimientos(
            db, delegacion, date_start, date_end,
            tipo, category_id, page, page_size
        )
        grafico_evolucion = cls.get_grafico_evolucion(
            db, delegacion, date_start, date_end
        )
        grafico_barras = cls.get_grafico_ingresos_egresos(
            db, delegacion, date_start, date_end
        )

        return {
            "saldo_actual": float(saldo),
            "ingresos_hoy": indicadores["ingresos_hoy"],
            "egresos_hoy": indicadores["egresos_hoy"],
            "transacciones_hoy": indicadores["transacciones_hoy"],
            "alertas": alertas,
            "movimientos": movimientos,
            "grafico_evolucion": grafico_evolucion,
            "grafico_ingresos_egresos": grafico_barras
        }
