import api from './api'
export default {
  getAll:             ()          => api.get('/config'),
  getBalance:         (deleg)     => api.get(`/config/balance/${deleg}`),
  create:             (data)      => api.post('/config', data),
  update:             (deleg, d)  => api.put(`/config/${deleg}`, d),
}
