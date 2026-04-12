/**
 * Parche M6 — Servicio Axios para adjuntos de transacciones.
 */
import api from './api'

export default {
  list(txnId) {
    return api.get(`/transactions/${txnId}/attachments`)
  },
  upload(txnId, file, onProgress) {
    const formData = new FormData()
    formData.append('file', file)
    return api.post(`/transactions/${txnId}/attachments`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: onProgress
    })
  },
  downloadUrl(txnId, attId) {
    const base = api.defaults.baseURL || '/api/v1'
    return `${base}/transactions/${txnId}/attachments/${attId}`
  },
  delete(txnId, attId) {
    return api.delete(`/transactions/${txnId}/attachments/${attId}`)
  }
}
