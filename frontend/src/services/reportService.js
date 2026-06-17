/**
 * Servicio de Informes — M8
 * Descarga de informes en PDF y Excel.
 */
import api from './api'

function triggerDownload(response, fallbackName) {
  const cd = response.headers['content-disposition'] || ''
  let filename = fallbackName
  const match = cd.match(/filename=(.+?)(?:;|$)/)
  if (match) filename = match[1]
  const url = window.URL.createObjectURL(new Blob([response.data]))
  const link = document.createElement('a')
  link.href = url
  link.setAttribute('download', filename)
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.URL.revokeObjectURL(url)
}

export default {
  /**
   * Descarga informe de cierre de sesión.
   */
  downloadSessionReport(sessionId, format = 'pdf') {
    return api.get(`/reports/session/${sessionId}`, {
      params: { format },
      responseType: 'blob'
    }).then(response => triggerDownload(response, `cierre_sesion_${sessionId}.${format}`))
  },

  /**
   * Descarga informe de período libre.
   */
  downloadPeriodReport(params = {}) {
    const format = params.format || 'pdf'
    return api.get('/reports/period', {
      params: { ...params, format },
      responseType: 'blob'
    }).then(response => triggerDownload(response, `informe_periodo_${params.date_start}_${params.date_end}.${format}`))
  },

  /**
   * Descarga informe por subcategoría.
   * Sin subcategory_id: resumen de todas las subcategorías.
   * Con subcategory_id: detalle de los movimientos de esa subcategoría.
   * @param {Object} params - { date_start, date_end, delegacion, subcategory_id, format }
   */
  downloadSubcategoryReport(params = {}) {
    const format = params.format || 'pdf'
    return api.get('/reports/by-subcategory', {
      params: { ...params, format },
      responseType: 'blob'
    }).then(response => triggerDownload(response, `informe_subcategoria_${params.date_start}_${params.date_end}.${format}`))
  }
}
