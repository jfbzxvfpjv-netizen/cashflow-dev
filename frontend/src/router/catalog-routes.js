/**
 * Módulo 4 — Rutas de catálogos.
 * Añadir estas rutas al array de routes del router principal (src/router/index.js).
 * Todas las rutas requieren autenticación. Las de escritura (crear/editar)
 * están protegidas por RBAC en el backend.
 */

// Importar vistas de catálogos
import ProjectsView from '@/views/catalogs/ProjectsView.vue'
import CategoriesView from '@/views/catalogs/CategoriesView.vue'
import SuppliersView from '@/views/catalogs/SuppliersView.vue'
import EmployeesView from '@/views/catalogs/EmployeesView.vue'
import PartnersView from '@/views/catalogs/PartnersView.vue'
import CorporateAccountsView from '@/views/catalogs/CorporateAccountsView.vue'
import VehiclesView from '@/views/catalogs/VehiclesView.vue'

/**
 * Rutas de catálogos — añadir como hijas de la ruta principal autenticada.
 *
 * Ejemplo de integración en router/index.js:
 *
 *   import { catalogRoutes } from './catalog-routes'
 *
 *   const routes = [
 *     { path: '/login', ... },
 *     {
 *       path: '/',
 *       component: MainLayout,
 *       meta: { requiresAuth: true },
 *       children: [
 *         { path: 'dashboard', ... },      // M8
 *         { path: 'sessions', ... },       // M5
 *         ...catalogRoutes,                // M4
 *       ]
 *     }
 *   ]
 */
export const catalogRoutes = [
  {
    path: 'projects',
    name: 'projects',
    component: ProjectsView,
    meta: { title: 'Proyectos', icon: 'folder', roles: ['admin'] },
  },
  {
    path: 'categories',
    name: 'categories',
    component: CategoriesView,
    meta: { title: 'Categorías', icon: 'tag', roles: ['admin'] },
  },
  {
    path: 'suppliers',
    name: 'suppliers',
    component: SuppliersView,
    meta: { title: 'Proveedores', icon: 'truck', roles: ['admin'] },
  },
  {
    path: 'employees',
    name: 'employees',
    component: EmployeesView,
    meta: { title: 'Empleados', icon: 'users', roles: ['admin', 'contable'] },
  },
  {
    path: 'partners',
    name: 'partners',
    component: PartnersView,
    meta: { title: 'Socios', icon: 'briefcase', roles: ['admin', 'contable'] },
  },
  {
    path: 'corporate-accounts',
    name: 'corporate-accounts',
    component: CorporateAccountsView,
    meta: { title: 'Cuentas Corporativas', icon: 'building', roles: ['admin'] },
  },
  {
    path: 'vehicles',
    name: 'vehicles',
    component: VehiclesView,
    meta: { title: 'Vehículos', icon: 'car', roles: ['admin'] },
  },
]

/**
 * Entradas para el menú lateral — filtrar por rol del usuario activo.
 * Usar en el componente SidebarMenu.vue:
 *
 *   import { catalogMenuItems } from './catalog-routes'
 *   const visibleItems = catalogMenuItems.filter(
 *     item => item.roles.includes(currentUser.role)
 *   )
 */
export const catalogMenuItems = [
  { label: 'Proyectos', path: '/projects', icon: 'folder', roles: ['admin'] },
  { label: 'Categorías', path: '/categories', icon: 'tag', roles: ['admin'] },
  { label: 'Proveedores', path: '/suppliers', icon: 'truck', roles: ['admin'] },
  { label: 'Empleados', path: '/employees', icon: 'users', roles: ['admin', 'contable'] },
  { label: 'Socios', path: '/partners', icon: 'briefcase', roles: ['admin', 'contable'] },
  { label: 'Cuentas', path: '/corporate-accounts', icon: 'building', roles: ['admin'] },
  { label: 'Vehículos', path: '/vehicles', icon: 'car', roles: ['admin'] },
]
