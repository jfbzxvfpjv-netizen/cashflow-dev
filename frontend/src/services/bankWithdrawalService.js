import api from './api'

export default {
  // Paso 1: SOLICITAR (gestor)
  request:      (data)          => api.post('/bank-withdrawals', data),
  // Paso 2: FORMALIZAR (contable)
  formalize:    (id, data)      => api.put(`/bank-withdrawals/${id}/formalize`, data),
  // Paso 3a: APROBAR (admin)
  approve:      (id, data = {}) => api.put(`/bank-withdrawals/${id}/approve`, data),
  // Paso 3b: RECHAZAR (admin)
  reject:       (id, data)      => api.put(`/bank-withdrawals/${id}/reject`, data),
  // Cancelar (gestor solicitante)
  cancel:       (id)            => api.put(`/bank-withdrawals/${id}/cancel`),
  // Paso 4: CONFIRMAR (gestor)
  confirm:      (id, data = {}) => api.put(`/bank-withdrawals/${id}/confirm`, data),
  // Lectura
  list:         (params = {})   => api.get('/bank-withdrawals', { params }),
  getById:      (id)            => api.get(`/bank-withdrawals/${id}`),
  pendingCount: ()              => api.get('/bank-withdrawals/pending-count'),
  // Backward compat
  propose:      (data)          => api.post('/bank-withdrawals', data),
}
