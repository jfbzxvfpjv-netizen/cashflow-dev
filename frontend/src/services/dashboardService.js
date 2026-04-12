/**
 * Servicio de Dashboard — M8
 * Llamada al endpoint GET /dashboard/summary
 */
import api from './api'

export default {
  /**
   * Obtiene todos los datos del dashboard en una sola llamada.
   * @param {Object} params - { delegacion, date_start, date_end, tipo, category_id, page, page_size }
   */
  getSummary(params = {}) {
    return api.get('/dashboard/summary', { params })
  }
}
