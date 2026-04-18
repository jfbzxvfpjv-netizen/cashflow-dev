// Servicios de los 8 módulos financieros especiales (M9)
import api from './api'

export const advancesService = {
  list: (params = {}) => api.get('/advances-loans', { params }).then(r => r.data),
  create: (data) => api.post('/advances-loans', data).then(r => r.data),
  repay: (id, data) => api.put(`/advances-loans/${id}/repay`, data).then(r => r.data),
}

export const retentionsService = {
  list: (params = {}) => api.get('/retentions-deposits', { params }).then(r => r.data),
  create: (data) => api.post('/retentions-deposits', data).then(r => r.data),
  release: (id, data) => api.put(`/retentions-deposits/${id}/release`, data).then(r => r.data),
}

export const floatsService = {
  list: (params = {}) => api.get('/floats', { params }).then(r => r.data),
  create: (data) => api.post('/floats', data).then(r => r.data),
  justify: (id, data) => api.put(`/floats/${id}/justify`, data).then(r => r.data),
  close: (id, data) => api.put(`/floats/${id}/close`, data).then(r => r.data),
}

export const installmentsService = {
  list: (params = {}) => api.get('/installments', { params }).then(r => r.data),
  create: (data) => api.post('/installments', data).then(r => r.data),
  pay: (id, data) => api.post(`/installments/${id}/pay`, data).then(r => r.data),
}

export const currencyService = {
  list: (params = {}) => api.get('/currency-ops', { params }).then(r => r.data),
  stock: (deleg) => api.get(`/currency-ops/eur-stock/${deleg}`).then(r => r.data),
  getStock: (deleg) => api.get(`/currency-ops/eur-stock/${deleg}`).then(r => r.data),
  buy: (data) => api.post('/currency-ops/buy', data).then(r => r.data),
  deliver: (data) => api.post('/currency-ops/deliver', data).then(r => r.data),
  edit: (id, data) => api.put(`/currency-ops/${id}`, data).then(r => r.data),
  cancel: (id, reason) => api.post(`/currency-ops/${id}/cancel`, { reason }).then(r => r.data),
}

export const partnerAccountsService = {
  balances: () => api.get('/partner-accounts/balances').then(r => r.data),
  movements: (params = {}) => api.get('/partner-accounts/movements', { params }).then(r => r.data),
  charge: (data) => api.post('/partner-accounts/charge', data).then(r => r.data),
  contribution: (data) => api.post('/partner-accounts/contribution', data).then(r => r.data),
  compensate: (data) => api.post('/partner-accounts/compensate', data).then(r => r.data),
}

export const reimbursableService = {
  list: (params = {}) => api.get('/reimbursable-expenses', { params }).then(r => r.data),
  create: (data) => api.post('/reimbursable-expenses', data).then(r => r.data),
  reimburse: (id, data) => api.put(`/reimbursable-expenses/${id}/reimburse`, data).then(r => r.data),
}

export const moneyTransfersService = {
  list: (params = {}) => api.get('/money-transfers', { params }).then(r => r.data),
  create: (data) => api.post('/money-transfers', data).then(r => r.data),
  position: () => api.get('/money-transfers/inter-delegation-position').then(r => r.data),
}