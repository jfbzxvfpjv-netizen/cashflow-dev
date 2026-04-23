/**
 * Módulo 6 — Servicio Axios para transacciones, aprobaciones e integridad.
 */
import api from './api'

export default {
  // --- Transacciones ---
  list(params = {}) {
    return api.get('/transactions', { params })
  },
  get(id) {
    return api.get(`/transactions/${id}`)
  },
  create(data) {
    return api.post('/transactions', data)
  },
  update(id, data) {
    return api.put(`/transactions/${id}`, data)
  },
  cancel(id, reason) {
    return api.delete(`/transactions/${id}`, { data: { reason } })
  },
  execute(id) {
    return api.put(`/transactions/${id}/execute`)
  },
  approve(id) {
    return api.put(`/transactions/${id}/approve`)
  },
  reject(id, reason) {
    return api.put(`/transactions/${id}/reject`, { reason })
  },

  // --- Umbrales de aprobación ---
  listThresholds() {
    return api.get('/approvals/thresholds')
  },
  createThreshold(data) {
    return api.post('/approvals/thresholds', data)
  },
  updateThreshold(id, data) {
    return api.put(`/approvals/thresholds/${id}`, data)
  },
  deleteThreshold(id) {
    return api.delete(`/approvals/thresholds/${id}`)
  },
  listPendingApprovals() {
    return api.get('/approvals/pending')
  },

  // --- Integridad ---
  verifyAll() {
    return api.get('/integrity/verify')
  },
  verifySingle(id) {
    return api.get(`/integrity/verify/${id}`)
  },

  // --- Catálogos para filtros (parche filtros M6) ---
  getCategories(params = {}) {
    return api.get('/categories', { params })
  },
  getSubcategories(params = {}) {
    return api.get('/subcategories', { params })
  },
  getSuppliers(params = {}) {
    return api.get('/suppliers', { params })
  },
  getEmployees(params = {}) {
    return api.get('/employees', { params })
  },
  getProjects(params = {}) {
    return api.get('/projects', { params })
  },
  getWorks(params = {}) {
    return api.get('/works', { params })
  },
  getPartners(params = {}) {
    return api.get('/partners', { params })
  },
}
