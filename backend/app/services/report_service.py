"""
Servicio de Informes — M8
Generación de informes de cierre de sesión y período libre
en formato PDF (WeasyPrint) y Excel (openpyxl).
"""
import io
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any

from sqlalchemy import cast, Date, func
from sqlalchemy.orm import Session

from app.models.cash_flow import (
    CashSession, Transaction, SystemConfig
)
from app.models.catalogs import (
    TransactionCategory, TransactionSubcategory,
    Supplier, Employee, Partner
)
from app.models.user import User


class ReportService:
    """Genera informes en PDF y Excel."""

    @staticmethod
    def _get_contraparte(db: Session, t: Transaction) -> str:
        """Obtiene el nombre de la contraparte de una transacción."""
        if t.counterparty_free:
            return t.counterparty_free
        if t.supplier_id:
            s = db.query(Supplier).filter(Supplier.id == t.supplier_id).first()
            return s.name if s else ''
        if t.employee_id:
            e = db.query(Employee).filter(Employee.id == t.employee_id).first()
            return e.full_name if e else ''
        if t.partner_id:
            p = db.query(Partner).filter(Partner.id == t.partner_id).first()
            return p.full_name if p else ''
        return ''

    @staticmethod
    def _format_amount(amount) -> str:
        """Formatea un importe numérico con separadores de miles."""
        try:
            val = float(amount)
            if val == int(val):
                return f"{int(val):,}".replace(",", ".")
            return f"{val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        except (ValueError, TypeError):
            return "0"

    @classmethod
    def get_session_data(cls, db: Session, session_id: int) -> Dict[str, Any]:
        """Obtiene todos los datos necesarios para el informe de sesión."""
        session = db.query(CashSession).filter(CashSession.id == session_id).first()
        if not session:
            return None

        user = db.query(User).filter(User.id == session.user_id).first()

        transactions = db.query(Transaction).filter(
            Transaction.session_id == session_id
        ).order_by(Transaction.created_at).all()

        items = []
        total_ingresos = Decimal('0')
        total_egresos = Decimal('0')

        for t in transactions:
            cat = db.query(TransactionCategory).filter(
                TransactionCategory.id == t.category_id
            ).first()

            contraparte = cls._get_contraparte(db, t)

            estado = 'Aprobada'
            if t.cancelled:
                estado = 'Anulada'
            elif t.approval_status == 'pending_approval':
                estado = 'Pendiente'
            elif t.approval_status == 'authorized':
                estado = 'Autorizada'
            elif t.approval_status == 'rejected':
                estado = 'Rechazada'

            if not t.cancelled and t.approval_status == 'approved':
                if t.type == 'income':
                    total_ingresos += t.amount
                else:
                    total_egresos += t.amount

            items.append({
                "fecha": t.created_at.strftime("%d/%m/%Y %H:%M") if t.created_at else '',
                "referencia": t.reference_number or '',
                "concepto": t.concept or '',
                "categoria": cat.name if cat else '',
                "contraparte": contraparte,
                "tipo": t.type,
                "importe": float(t.amount),
                "estado": estado,
                "cancelled": t.cancelled
            })

        return {
            "session": {
                "id": session.id,
                "delegacion": session.delegacion,
                "gestor": user.full_name if user else '',
                "opened_at": session.opened_at.strftime("%d/%m/%Y %H:%M") if session.opened_at else '',
                "closed_at": session.closed_at.strftime("%d/%m/%Y %H:%M") if session.closed_at else 'Abierta',
                "opening_balance": float(session.opening_balance),
                "closing_balance": float(session.closing_balance) if session.closing_balance is not None else None,
                "status": session.status
            },
            "transactions": items,
            "total_ingresos": float(total_ingresos),
            "total_egresos": float(total_egresos),
            "diferencia": float(total_ingresos - total_egresos)
        }

    @classmethod
    def get_period_data(
        cls, db: Session,
        delegacion: Optional[str],
        date_start: date,
        date_end: date,
        category_id: Optional[int] = None,
        project_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Obtiene datos para el informe de período libre."""
        query = db.query(Transaction).filter(
            cast(Transaction.created_at, Date) >= date_start,
            cast(Transaction.created_at, Date) <= date_end
        )
        if delegacion and delegacion != 'Consolidado':
            query = query.filter(Transaction.delegacion == delegacion)
        if category_id:
            query = query.filter(Transaction.category_id == category_id)

        transactions = query.order_by(Transaction.created_at).all()

        items = []
        total_ingresos = Decimal('0')
        total_egresos = Decimal('0')

        for t in transactions:
            cat = db.query(TransactionCategory).filter(
                TransactionCategory.id == t.category_id
            ).first()
            contraparte = cls._get_contraparte(db, t)

            estado = 'Aprobada'
            if t.cancelled:
                estado = 'Anulada'
            elif t.approval_status == 'pending_approval':
                estado = 'Pendiente'
            elif t.approval_status == 'authorized':
                estado = 'Autorizada'
            elif t.approval_status == 'rejected':
                estado = 'Rechazada'

            if not t.cancelled and t.approval_status == 'approved':
                if t.type == 'income':
                    total_ingresos += t.amount
                else:
                    total_egresos += t.amount

            items.append({
                "fecha": t.created_at.strftime("%d/%m/%Y %H:%M") if t.created_at else '',
                "referencia": t.reference_number or '',
                "concepto": t.concept or '',
                "categoria": cat.name if cat else '',
                "contraparte": contraparte,
                "tipo": t.type,
                "importe": float(t.amount),
                "estado": estado,
                "delegacion": t.delegacion,
                "cancelled": t.cancelled
            })

        filtros_texto = []
        if delegacion:
            filtros_texto.append(f"Delegación: {delegacion}")
        if category_id:
            cat = db.query(TransactionCategory).filter(TransactionCategory.id == category_id).first()
            filtros_texto.append(f"Categoría: {cat.name if cat else category_id}")

        return {
            "periodo": {
                "date_start": date_start.strftime("%d/%m/%Y"),
                "date_end": date_end.strftime("%d/%m/%Y"),
                "delegacion": delegacion or "Todas",
                "filtros": ", ".join(filtros_texto) if filtros_texto else "Sin filtros"
            },
            "transactions": items,
            "total_ingresos": float(total_ingresos),
            "total_egresos": float(total_egresos),
            "saldo_neto": float(total_ingresos - total_egresos)
        }

    @classmethod
    def generate_session_pdf(cls, db: Session, session_id: int) -> Optional[bytes]:
        """Genera informe de cierre de sesión en PDF."""
        data = cls.get_session_data(db, session_id)
        if not data:
            return None

        s = data["session"]
        rows_html = ""
        for t in data["transactions"]:
            color = "#16a34a" if t["tipo"] == "income" else "#dc2626"
            if t["cancelled"]:
                color = "#9ca3af"
            signo = "+" if t["tipo"] == "income" else "-"
            rows_html += f"""
            <tr style="{'text-decoration:line-through;color:#9ca3af;' if t['cancelled'] else ''}">
                <td>{t['fecha']}</td>
                <td>{t['referencia']}</td>
                <td>{t['concepto'][:60]}</td>
                <td>{t['categoria']}</td>
                <td>{t['contraparte'][:30]}</td>
                <td style="color:{color};text-align:right;font-weight:600;">{signo} {cls._format_amount(t['importe'])} XAF</td>
                <td>{t['estado']}</td>
            </tr>"""

        html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
    @page {{ size: A4 landscape; margin: 15mm; }}
    body {{ font-family: Arial, Helvetica, sans-serif; font-size: 10px; color: #1e293b; }}
    h1 {{ font-size: 16px; color: #1e40af; margin-bottom: 5px; }}
    h2 {{ font-size: 12px; color: #475569; margin-top: 0; }}
    .header-grid {{ display: flex; justify-content: space-between; margin-bottom: 15px; }}
    .header-box {{ background: #f1f5f9; padding: 8px 12px; border-radius: 4px; }}
    .header-box span {{ display: block; font-size: 9px; color: #64748b; }}
    .header-box strong {{ font-size: 13px; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
    th {{ background: #1e40af; color: white; padding: 6px 8px; text-align: left; font-size: 9px; }}
    td {{ padding: 5px 8px; border-bottom: 1px solid #e2e8f0; font-size: 9px; }}
    tr:nth-child(even) {{ background: #f8fafc; }}
    .totals {{ margin-top: 15px; text-align: right; }}
    .totals div {{ margin: 3px 0; font-size: 11px; }}
    .footer {{ margin-top: 20px; font-size: 8px; color: #94a3b8; text-align: center; }}
</style></head><body>
    <h1>Informe de Cierre de Sesión</h1>
    <h2>Delegación: {s['delegacion']} — Sesión #{s['id']}</h2>

    <div style="display:flex;gap:20px;margin-bottom:15px;">
        <div class="header-box"><span>Gestor</span><strong>{s['gestor']}</strong></div>
        <div class="header-box"><span>Apertura</span><strong>{s['opened_at']}</strong></div>
        <div class="header-box"><span>Cierre</span><strong>{s['closed_at']}</strong></div>
        <div class="header-box"><span>Saldo apertura</span><strong>{cls._format_amount(s['opening_balance'])} XAF</strong></div>
        <div class="header-box"><span>Saldo cierre</span><strong>{cls._format_amount(s['closing_balance']) if s['closing_balance'] is not None else 'N/A'} XAF</strong></div>
    </div>

    <table>
        <thead><tr>
            <th>Fecha/Hora</th><th>Ref.</th><th>Concepto</th>
            <th>Categoría</th><th>Contraparte</th><th style="text-align:right">Importe</th><th>Estado</th>
        </tr></thead>
        <tbody>{rows_html}</tbody>
    </table>

    <div class="totals">
        <div style="color:#16a34a;">Total ingresos: <strong>{cls._format_amount(data['total_ingresos'])} XAF</strong></div>
        <div style="color:#dc2626;">Total egresos: <strong>{cls._format_amount(data['total_egresos'])} XAF</strong></div>
        <div style="color:#1e40af;font-size:13px;">Diferencia: <strong>{cls._format_amount(data['diferencia'])} XAF</strong></div>
    </div>

    <div class="footer">
        Generado automáticamente — {datetime.now().strftime('%d/%m/%Y %H:%M')} — Sistema de Gestión de Flujo de Caja
    </div>
</body></html>"""

        try:
            from weasyprint import HTML as WeasyHTML
            return WeasyHTML(string=html).write_pdf()
        except Exception:
            # Fallback: devolver HTML como bytes si WeasyPrint no disponible
            return html.encode('utf-8')

    @classmethod
    def generate_session_xlsx(cls, db: Session, session_id: int) -> Optional[bytes]:
        """Genera informe de cierre de sesión en Excel."""
        data = cls.get_session_data(db, session_id)
        if not data:
            return None

        from openpyxl import Workbook
        from openpyxl.styles import Font, Alignment, PatternFill, Border, Side

        wb = Workbook()
        ws = wb.active
        ws.title = f"Sesión {session_id}"

        # Estilos
        header_font = Font(bold=True, size=14, color="1E40AF")
        sub_font = Font(bold=True, size=10, color="475569")
        th_font = Font(bold=True, size=9, color="FFFFFF")
        th_fill = PatternFill(start_color="1E40AF", end_color="1E40AF", fill_type="solid")
        border = Border(bottom=Side(style='thin', color='E2E8F0'))

        # Cabecera
        s = data["session"]
        ws.merge_cells('A1:G1')
        ws['A1'] = "Informe de Cierre de Sesión"
        ws['A1'].font = header_font

        ws['A3'] = "Delegación:"
        ws['B3'] = s['delegacion']
        ws['A4'] = "Gestor:"
        ws['B4'] = s['gestor']
        ws['D3'] = "Apertura:"
        ws['E3'] = s['opened_at']
        ws['D4'] = "Cierre:"
        ws['E4'] = s['closed_at']
        ws['A5'] = "Saldo apertura:"
        ws['B5'] = s['opening_balance']
        ws['D5'] = "Saldo cierre:"
        ws['E5'] = s['closing_balance'] if s['closing_balance'] is not None else 'N/A'

        for cell in ['A3','A4','A5','D3','D4','D5']:
            ws[cell].font = Font(bold=True, size=9)

        # Encabezados de tabla
        headers = ['Fecha/Hora', 'Referencia', 'Concepto', 'Categoría', 'Contraparte', 'Importe', 'Estado']
        for col, h in enumerate(headers, 1):
            cell = ws.cell(row=7, column=col, value=h)
            cell.font = th_font
            cell.fill = th_fill
            cell.alignment = Alignment(horizontal='center')

        # Datos
        for i, t in enumerate(data["transactions"], 8):
            ws.cell(row=i, column=1, value=t['fecha'])
            ws.cell(row=i, column=2, value=t['referencia'])
            ws.cell(row=i, column=3, value=t['concepto'])
            ws.cell(row=i, column=4, value=t['categoria'])
            ws.cell(row=i, column=5, value=t['contraparte'])
            amt_cell = ws.cell(row=i, column=6, value=t['importe'])
            amt_cell.number_format = '#,##0'
            if t['tipo'] == 'income':
                amt_cell.font = Font(color="16A34A", bold=True)
            else:
                amt_cell.font = Font(color="DC2626", bold=True)
            ws.cell(row=i, column=7, value=t['estado'])
            for col in range(1, 8):
                ws.cell(row=i, column=col).border = border

        # Totales
        last_row = 8 + len(data["transactions"])
        ws.cell(row=last_row + 1, column=5, value="Total ingresos:").font = Font(bold=True)
        ws.cell(row=last_row + 1, column=6, value=data['total_ingresos']).font = Font(color="16A34A", bold=True)
        ws.cell(row=last_row + 2, column=5, value="Total egresos:").font = Font(bold=True)
        ws.cell(row=last_row + 2, column=6, value=data['total_egresos']).font = Font(color="DC2626", bold=True)
        ws.cell(row=last_row + 3, column=5, value="Diferencia:").font = Font(bold=True, size=11)
        ws.cell(row=last_row + 3, column=6, value=data['diferencia']).font = Font(bold=True, size=11, color="1E40AF")

        for col_num in [6]:
            for row in [last_row+1, last_row+2, last_row+3]:
                ws.cell(row=row, column=col_num).number_format = '#,##0'

        # Ajustar anchos
        ws.column_dimensions['A'].width = 18
        ws.column_dimensions['B'].width = 12
        ws.column_dimensions['C'].width = 40
        ws.column_dimensions['D'].width = 20
        ws.column_dimensions['E'].width = 25
        ws.column_dimensions['F'].width = 18
        ws.column_dimensions['G'].width = 12

        buffer = io.BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        return buffer.getvalue()

    @classmethod
    def generate_period_pdf(
        cls, db: Session,
        delegacion: Optional[str],
        date_start: date,
        date_end: date,
        category_id: Optional[int] = None,
        project_id: Optional[int] = None
    ) -> bytes:
        """Genera informe de período libre en PDF."""
        data = cls.get_period_data(db, delegacion, date_start, date_end, category_id, project_id)
        p = data["periodo"]

        rows_html = ""
        for t in data["transactions"]:
            color = "#16a34a" if t["tipo"] == "income" else "#dc2626"
            if t["cancelled"]:
                color = "#9ca3af"
            signo = "+" if t["tipo"] == "income" else "-"
            rows_html += f"""
            <tr style="{'text-decoration:line-through;color:#9ca3af;' if t['cancelled'] else ''}">
                <td>{t['fecha']}</td>
                <td>{t['referencia']}</td>
                <td>{t['concepto'][:60]}</td>
                <td>{t['categoria']}</td>
                <td>{t['contraparte'][:30]}</td>
                <td style="color:{color};text-align:right;font-weight:600;">{signo} {cls._format_amount(t['importe'])} XAF</td>
                <td>{t['delegacion']}</td>
                <td>{t['estado']}</td>
            </tr>"""

        html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
    @page {{ size: A4 landscape; margin: 15mm; }}
    body {{ font-family: Arial, Helvetica, sans-serif; font-size: 10px; color: #1e293b; }}
    h1 {{ font-size: 16px; color: #1e40af; margin-bottom: 5px; }}
    h2 {{ font-size: 12px; color: #475569; margin-top: 0; }}
    .info {{ background: #f1f5f9; padding: 8px 12px; border-radius: 4px; margin-bottom: 15px; font-size: 10px; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
    th {{ background: #1e40af; color: white; padding: 6px 8px; text-align: left; font-size: 9px; }}
    td {{ padding: 5px 8px; border-bottom: 1px solid #e2e8f0; font-size: 9px; }}
    tr:nth-child(even) {{ background: #f8fafc; }}
    .totals {{ margin-top: 15px; text-align: right; }}
    .totals div {{ margin: 3px 0; font-size: 11px; }}
    .footer {{ margin-top: 20px; font-size: 8px; color: #94a3b8; text-align: center; }}
</style></head><body>
    <h1>Informe de Período</h1>
    <h2>{p['date_start']} — {p['date_end']}</h2>
    <div class="info">
        <strong>Delegación:</strong> {p['delegacion']} &nbsp; | &nbsp;
        <strong>Filtros:</strong> {p['filtros']} &nbsp; | &nbsp;
        <strong>Total transacciones:</strong> {len(data['transactions'])}
    </div>

    <table>
        <thead><tr>
            <th>Fecha/Hora</th><th>Ref.</th><th>Concepto</th><th>Categoría</th>
            <th>Contraparte</th><th style="text-align:right">Importe</th><th>Deleg.</th><th>Estado</th>
        </tr></thead>
        <tbody>{rows_html}</tbody>
    </table>

    <div class="totals">
        <div style="color:#16a34a;">Total ingresos: <strong>{cls._format_amount(data['total_ingresos'])} XAF</strong></div>
        <div style="color:#dc2626;">Total egresos: <strong>{cls._format_amount(data['total_egresos'])} XAF</strong></div>
        <div style="color:#1e40af;font-size:13px;">Saldo neto: <strong>{cls._format_amount(data['saldo_neto'])} XAF</strong></div>
    </div>

    <div class="footer">
        Generado automáticamente — {datetime.now().strftime('%d/%m/%Y %H:%M')} — Sistema de Gestión de Flujo de Caja
    </div>
</body></html>"""

        try:
            from weasyprint import HTML as WeasyHTML
            return WeasyHTML(string=html).write_pdf()
        except Exception:
            return html.encode('utf-8')

    @classmethod
    def generate_period_xlsx(
        cls, db: Session,
        delegacion: Optional[str],
        date_start: date,
        date_end: date,
        category_id: Optional[int] = None,
        project_id: Optional[int] = None
    ) -> bytes:
        """Genera informe de período libre en Excel."""
        data = cls.get_period_data(db, delegacion, date_start, date_end, category_id, project_id)

        from openpyxl import Workbook
        from openpyxl.styles import Font, Alignment, PatternFill, Border, Side

        wb = Workbook()
        ws = wb.active
        ws.title = "Informe de Período"

        header_font = Font(bold=True, size=14, color="1E40AF")
        th_font = Font(bold=True, size=9, color="FFFFFF")
        th_fill = PatternFill(start_color="1E40AF", end_color="1E40AF", fill_type="solid")
        border = Border(bottom=Side(style='thin', color='E2E8F0'))

        p = data["periodo"]
        ws.merge_cells('A1:H1')
        ws['A1'] = "Informe de Período"
        ws['A1'].font = header_font

        ws['A3'] = "Período:"
        ws['B3'] = f"{p['date_start']} — {p['date_end']}"
        ws['A4'] = "Delegación:"
        ws['B4'] = p['delegacion']
        ws['A5'] = "Filtros:"
        ws['B5'] = p['filtros']
        for cell in ['A3','A4','A5']:
            ws[cell].font = Font(bold=True, size=9)

        headers = ['Fecha/Hora', 'Referencia', 'Concepto', 'Categoría', 'Contraparte', 'Importe', 'Delegación', 'Estado']
        for col, h in enumerate(headers, 1):
            cell = ws.cell(row=7, column=col, value=h)
            cell.font = th_font
            cell.fill = th_fill
            cell.alignment = Alignment(horizontal='center')

        for i, t in enumerate(data["transactions"], 8):
            ws.cell(row=i, column=1, value=t['fecha'])
            ws.cell(row=i, column=2, value=t['referencia'])
            ws.cell(row=i, column=3, value=t['concepto'])
            ws.cell(row=i, column=4, value=t['categoria'])
            ws.cell(row=i, column=5, value=t['contraparte'])
            amt = ws.cell(row=i, column=6, value=t['importe'])
            amt.number_format = '#,##0'
            if t['tipo'] == 'income':
                amt.font = Font(color="16A34A", bold=True)
            else:
                amt.font = Font(color="DC2626", bold=True)
            ws.cell(row=i, column=7, value=t['delegacion'])
            ws.cell(row=i, column=8, value=t['estado'])
            for col in range(1, 9):
                ws.cell(row=i, column=col).border = border

        last_row = 8 + len(data["transactions"])
        ws.cell(row=last_row+1, column=5, value="Total ingresos:").font = Font(bold=True)
        ws.cell(row=last_row+1, column=6, value=data['total_ingresos']).font = Font(color="16A34A", bold=True)
        ws.cell(row=last_row+2, column=5, value="Total egresos:").font = Font(bold=True)
        ws.cell(row=last_row+2, column=6, value=data['total_egresos']).font = Font(color="DC2626", bold=True)
        ws.cell(row=last_row+3, column=5, value="Saldo neto:").font = Font(bold=True, size=11)
        ws.cell(row=last_row+3, column=6, value=data['saldo_neto']).font = Font(bold=True, size=11, color="1E40AF")

        for row in [last_row+1, last_row+2, last_row+3]:
            ws.cell(row=row, column=6).number_format = '#,##0'

        ws.column_dimensions['A'].width = 18
        ws.column_dimensions['B'].width = 12
        ws.column_dimensions['C'].width = 40
        ws.column_dimensions['D'].width = 20
        ws.column_dimensions['E'].width = 25
        ws.column_dimensions['F'].width = 18
        ws.column_dimensions['G'].width = 12
        ws.column_dimensions['H'].width = 12

        buffer = io.BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        return buffer.getvalue()
