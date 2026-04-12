/**
 * Rutas M5 — Importar en router/index.js:
 *   import { m5Routes } from './m5_routes'
 *   routes: [...existentes, ...m5Routes]
 */
export const m5Routes = [
  { path: '/sessions', name: 'sessions', component: () => import('@/views/SessionsView.vue'), meta: { requiresAuth: true, title: 'Sesiones de caja' } },
  { path: '/config', name: 'config', component: () => import('@/views/ConfigView.vue'), meta: { requiresAuth: true, roles: ['admin'], title: 'Configuración' } },
  { path: '/bank-withdrawals', name: 'bank-withdrawals', component: () => import('@/views/BankWithdrawalsView.vue'), meta: { requiresAuth: true, roles: ['contable','admin','gestor'], title: 'Retiradas bancarias' } },
]
