/**
 * Servicio de Informes — M8
 * Descarga de informes en PDF y Excel.
 */
import api from './api'

export default {
  /**
   * Descarga informe de cierre de sesión.
   * @param {number} sessionId
   * @param {string} format - 'pdf' o 'xlsx'
   */
  downloadSessionReport(sessionId, format = 'pdf') {
    return api.get(`/reports/session/${sessionId}`, {
      params: { format },
      responseType: 'blob'
    }).then(response => {
      const contentDisposition = response.headers['content-disposition'] || ''
      let filename = `cierre_sesion_${sessionId}.${format}`
      const match = contentDisposition.match(/filename=(.+?)(?:;|$)/)
      if (match) filename = match[1]

      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', filename)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    })
  },

  /**
   * Descarga informe de período libre.
   * @param {Object} params - { date_start, date_end, delegacion, category_id, project_id, format }
   */
  downloadPeriodReport(params = {}) {
    const format = params.format || 'pdf'
    return api.get('/reports/period', {
      params: { ...params, format },
      responseType: 'blob'
    }).then(response => {
      const filename = `informe_periodo_${params.date_start}_${params.date_end}.${format}`
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', filename)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    })
  }
}
