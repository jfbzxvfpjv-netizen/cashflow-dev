import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import LoginView from '@/views/LoginView.vue'

// M3 — Vistas de autenticación y usuarios
const DashboardView = () => import('@/views/DashboardView.vue')
const UsersView = () => import('@/views/UsersView.vue')
const UserFormView = () => import('@/views/UserFormView.vue')
const ChangePasswordView = () => import('@/views/ChangePasswordView.vue')

// M4 — Vistas de catálogos
const ProjectsView = () => import('@/views/catalogs/ProjectsView.vue')
const CategoriesView = () => import('@/views/catalogs/CategoriesView.vue')
const SuppliersView = () => import('@/views/catalogs/SuppliersView.vue')
const EmployeesView = () => import('@/views/catalogs/EmployeesView.vue')
const PartnersView = () => import('@/views/catalogs/PartnersView.vue')
const CorporateAccountsView = () => import('@/views/catalogs/CorporateAccountsView.vue')
const VehiclesView = () => import('@/views/catalogs/VehiclesView.vue')

// M5 — Vistas de sesiones, configuración y retiradas
const SessionsView = () => import('@/views/SessionsView.vue')
const ConfigView = () => import('@/views/ConfigView.vue')
const BankWithdrawalsView = () => import('@/views/BankWithdrawalsView.vue')


// --- M6: Transacciones, aprobaciones e integridad ---
const TransactionsView = () => import('@/views/TransactionsView.vue')
const TransactionNewView = () => import('@/views/TransactionNewView.vue')
const TransactionDetailView = () => import('@/views/TransactionDetailView.vue')
const ApprovalsView = () => import('@/views/ApprovalsView.vue')
const IntegrityView = () => import('@/views/IntegrityView.vue')

const ImportView = () => import('@/views/ImportView.vue')
const DevView = () => import('@/views/DevView.vue')

const ReportsView = () => import('@/views/ReportsView.vue')
// M9 — Módulos financieros especiales (lazy)
const AdvancesLoansView        = () => import('@/views/AdvancesLoansView.vue')
const RetentionsDepositsView   = () => import('@/views/RetentionsDepositsView.vue')
const FloatsView               = () => import('@/views/FloatsView.vue')
const InstallmentsView         = () => import('@/views/InstallmentsView.vue')
const CurrencyView             = () => import('@/views/CurrencyView.vue')
const PartnerAccountsView      = () => import('@/views/PartnerAccountsView.vue')
const ReimbursableExpensesView = () => import('@/views/ReimbursableExpensesView.vue')
const MoneyTransfersView       = () => import('@/views/MoneyTransfersView.vue')

const routes = [
  { path: '/login', name: 'login', component: LoginView, meta: { requiresAuth: false } },
  { path: '/', redirect: '/dashboard' },

  // M3 — Dashboard y usuarios
  { path: '/dashboard', name: 'dashboard', component: DashboardView, meta: { requiresAuth: true, roles: [] } },
  { path: '/users', name: 'users', component: UsersView, meta: { requiresAuth: true, roles: ['admin'] } },
  { path: '/users/new', name: 'user-create', component: UserFormView, meta: { requiresAuth: true, roles: ['admin'] } },
  { path: '/users/:id/edit', name: 'user-edit', component: UserFormView, meta: { requiresAuth: true, roles: ['admin'] }, props: true },
  { path: '/change-password', name: 'change-password', component: ChangePasswordView, meta: { requiresAuth: true, roles: [] } },

  // M4 — Catálogos
  { path: '/projects', name: 'projects', component: ProjectsView, meta: { requiresAuth: true, roles: ['admin'] } },
  { path: '/categories', name: 'categories', component: CategoriesView, meta: { requiresAuth: true, roles: ['admin'] } },
  { path: '/suppliers', name: 'suppliers', component: SuppliersView, meta: { requiresAuth: true, roles: ['admin'] } },
  { path: '/employees', name: 'employees', component: EmployeesView, meta: { requiresAuth: true, roles: ['admin', 'contable'] } },
  { path: '/partners', name: 'partners', component: PartnersView, meta: { requiresAuth: true, roles: ['admin', 'contable'] } },
  { path: '/corporate-accounts', name: 'corporate-accounts', component: CorporateAccountsView, meta: { requiresAuth: true, roles: ['admin'] } },
  { path: '/vehicles', name: 'vehicles', component: VehiclesView, meta: { requiresAuth: true, roles: ['admin'] } },

  // M5 — Sesiones de caja, configuración y retiradas
  { path: '/sessions', name: 'sessions', component: SessionsView, meta: { requiresAuth: true, roles: ['gestor', 'admin'] } },
  { path: '/config', name: 'config', component: ConfigView, meta: { requiresAuth: true, roles: ['admin'] } },
  { path: '/bank-withdrawals', name: 'bank-withdrawals', component: BankWithdrawalsView, meta: { requiresAuth: true, roles: ['contable', 'admin', 'gestor'] } },

  // M6 — Transacciones (se añadirá aquí)

  
    // --- M6: Transacciones ---
    { path: '/transactions', name: 'transactions', component: TransactionsView, meta: { requiresAuth: true } },
    { path: '/transactions/new', name: 'transaction-new', component: TransactionNewView, meta: { requiresAuth: true, roles: ['admin', 'gestor'] } },
    { path: '/transactions/:id', name: 'transaction-detail', component: TransactionDetailView, meta: { requiresAuth: true } },
    { path: '/approvals', name: 'approvals', component: ApprovalsView, meta: { requiresAuth: true, roles: ['admin'] } },
    { path: '/integrity', name: 'integrity', component: IntegrityView, meta: { requiresAuth: true, roles: ['admin'] } },
        { path: '/import', name: 'import', component: ImportView, meta: { requiresAuth: true, roles: ['admin'] } },
    { path: '/dev', name: 'dev', component: DevView, meta: { requiresAuth: true, roles: ['admin'] } },
    { path: '/reports', name: 'reports', component: ReportsView, meta: { requiresAuth: true, roles: ['admin','contable','gestor','consulta'] } },
    { path: '/:pathMatch(.*)*', name: 'not-found', redirect: '/dashboard' },

    {
      path: '/admin/backups',
      name: 'admin-backups',
      component: () => import('../views/admin/BackupsView.vue'),
      meta: { requiresAuth: true, roles: ['admin'] }
    },
  // M9: Módulos financieros especiales
  { path: '/advances-loans',       name: 'AdvancesLoans',        component: AdvancesLoansView,        meta: { requiresAuth: true } },
  { path: '/retentions-deposits',  name: 'RetentionsDeposits',   component: RetentionsDepositsView,   meta: { requiresAuth: true } },
  { path: '/floats',               name: 'Floats',               component: FloatsView,               meta: { requiresAuth: true } },
  { path: '/installments',         name: 'Installments',         component: InstallmentsView,         meta: { requiresAuth: true } },
  { path: '/currency-ops',         name: 'CurrencyOps',          component: CurrencyView,             meta: { requiresAuth: true } },
  { path: '/partner-accounts',     name: 'PartnerAccounts',      component: PartnerAccountsView,      meta: { requiresAuth: true } },
  { path: '/reimbursable-expenses',name: 'ReimbursableExpenses', component: ReimbursableExpensesView, meta: { requiresAuth: true } },
  { path: '/money-transfers',      name: 'MoneyTransfers',       component: MoneyTransfersView,       meta: { requiresAuth: true } },
]

const router = createRouter({ history: createWebHistory(), routes })

router.beforeEach(async (to, from, next) => {
  const auth = useAuthStore()
  if (to.meta.requiresAuth === false) {
    return auth.isAuthenticated ? next({ name: 'dashboard' }) : next()
  }
  if (!auth.isAuthenticated) return next({ name: 'login', query: { redirect: to.fullPath } })
  const allowed = to.meta.roles
  if (allowed && allowed.length > 0 && !auth.hasRole(...allowed)) return next({ name: 'dashboard' })
  next()
})

export default router
