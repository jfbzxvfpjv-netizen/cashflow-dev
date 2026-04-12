/**
 * Servicio Axios para el módulo de importación desde Excel.
 * Gestiona la validación, ejecución e historial de importaciones.
 */
import api from './api'

export default {
  /**
   * Valida un fichero Excel sin importar.
   * @param {File} file - Fichero .xlsx
   * @param {string} delegacion - 'Bata' o 'Malabo'
   */
  validate(file, delegacion) {
    const formData = new FormData()
    formData.append('file', file)
    return api.post(`/import/validate?delegacion=${delegacion}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },

  /**
   * Ejecuta la importación tras validación exitosa.
   * @param {File} file - Fichero .xlsx
   * @param {string} delegacion - 'Bata' o 'Malabo'
   */
  execute(file, delegacion) {
    const formData = new FormData()
    formData.append('file', file)
    return api.post(`/import/execute?delegacion=${delegacion}&confirmed=true`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },

  /** Obtiene el historial de importaciones. */
  getHistory() {
    return api.get('/import/history')
  }
}
