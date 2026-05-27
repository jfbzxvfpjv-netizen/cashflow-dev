import api from './api'

export default {
  listPeriods(params = {}) {
    return api.get('/payrolls', { params })
  },
  getPeriod(periodId) {
    return api.get(`/payrolls/${periodId}`)
  },
  generatePeriod(data) {
    return api.post('/payrolls', data)
  },
  updateEntry(periodId, entryId, data) {
    return api.put(`/payrolls/${periodId}/entries/${entryId}`, data)
  },
  executePayments(periodId, entryIds = null) {
    return api.post(`/payrolls/${periodId}/execute`, { entry_ids: entryIds })
  },
  payEntry(periodId, entryId, signaturePayload) {
    return api.post(`/payrolls/${periodId}/entries/${entryId}/pay`, { signature: signaturePayload })
  },
  closePeriod(periodId) {
    return api.put(`/payrolls/${periodId}/close`)
  },
}
