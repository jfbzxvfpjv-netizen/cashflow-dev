"""
Router principal — /api/v1
Centraliza todos los routers de la API. Cada módulo añade su router aquí.
"""

from fastapi import APIRouter

# M3 — Autenticación y gestión de usuarios
from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router

# M4 — Catálogos
from app.routers.projects import router as projects_router
from app.routers.works import router as works_router
from app.routers.categories import router as categories_router
from app.routers.subcategories import router as subcategories_router
from app.routers.suppliers import router as suppliers_router
from app.routers.employees import router as employees_router
from app.routers.partners import router as partners_router
from app.routers.corporate_accounts import router as corporate_accounts_router
from app.routers.vehicles import router as vehicles_router

api_router = APIRouter(prefix="/api/v1")

# M3
api_router.include_router(auth_router)
api_router.include_router(users_router)

# M4 — Catálogos
api_router.include_router(projects_router)
api_router.include_router(works_router)
api_router.include_router(categories_router)
api_router.include_router(subcategories_router)
api_router.include_router(suppliers_router)
api_router.include_router(employees_router)
api_router.include_router(partners_router)
api_router.include_router(corporate_accounts_router)
api_router.include_router(vehicles_router)

# M5 — Sesiones de caja (se añadirá aquí)
# M6 — Transacciones (se añadirá aquí)

# M5 — Sesiones, configuración y retiradas bancarias
from app.routers.config import router as config_router
from app.routers.sessions import router as sessions_router
from app.routers.bank_withdrawals import router as bank_withdrawals_router

api_router.include_router(config_router)
api_router.include_router(sessions_router)
api_router.include_router(bank_withdrawals_router)

# M5 — Sesiones, configuración y retiradas bancarias
from app.routers.config import router as config_router
from app.routers.sessions import router as sessions_router
from app.routers.bank_withdrawals import router as bank_withdrawals_router

api_router.include_router(config_router)
api_router.include_router(sessions_router)
api_router.include_router(bank_withdrawals_router)

# --- M6: Transacciones, aprobaciones e integridad ---
from app.routers.transactions import router as transactions_router
api_router.include_router(transactions_router)
from app.routers.approvals import router as approvals_router
api_router.include_router(approvals_router)
from app.routers.integrity import router as integrity_router
api_router.include_router(integrity_router)

# --- Parche M6: Adjuntos ---
from app.routers.attachments import router as attachments_router
api_router.include_router(attachments_router)

from app.routers.import_router import router as import_router
api_router.include_router(import_router)

from app.routers.dev_router import router as dev_router
api_router.include_router(dev_router)

# M8 — Dashboard
from app.routers.dashboard import router as dashboard_router
api_router.include_router(dashboard_router)

# M8 — Informes
from app.routers.reports import router as reports_router
# M9 — Módulos financieros especiales
from app.routers.advances import router as advances_router
from app.routers.retentions import router as retentions_router
from app.routers.floats import router as floats_router
from app.routers.installments import router as installments_router
from app.routers.currency import router as currency_router
from app.routers.partner_accounts import router as partner_accounts_router
from app.routers.reimbursable import router as reimbursable_router
from app.routers.money_transfers import router as money_transfers_router
api_router.include_router(reports_router)

# --- M9: Módulos financieros especiales ---
api_router.include_router(advances_router)
api_router.include_router(retentions_router)
api_router.include_router(floats_router)
api_router.include_router(installments_router)
api_router.include_router(currency_router)
api_router.include_router(partner_accounts_router)
api_router.include_router(reimbursable_router)
api_router.include_router(money_transfers_router)

