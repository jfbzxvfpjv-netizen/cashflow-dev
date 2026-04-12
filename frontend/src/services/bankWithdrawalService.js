import api from './api'
export default {
  propose:      (data)          => api.post('/bank-withdrawals', data),
  approve:      (id, data = {}) => api.put(`/bank-withdrawals/${id}/approve`, data),
  reject:       (id, data)      => api.put(`/bank-withdrawals/${id}/reject`, data),
  confirm:      (id, data = {}) => api.put(`/bank-withdrawals/${id}/confirm`, data),
  list:         (params = {})   => api.get('/bank-withdrawals', { params }),
  getById:      (id)            => api.get(`/bank-withdrawals/${id}`),
  pendingCount: (deleg = null)  => api.get('/bank-withdrawals/pending-count', { params: deleg ? { delegacion: deleg } : {} }),
}
