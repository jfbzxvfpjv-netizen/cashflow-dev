import api from './api'
export default {
  open:      (data = {})    => api.post('/sessions', data),
  close:     (id, data = {})=> api.put(`/sessions/${id}/close`, data),
  getActive: ()             => api.get('/sessions/active'),
  list:      (params = {})  => api.get('/sessions', { params }),
  getById:   (id)           => api.get(`/sessions/${id}`),
}
