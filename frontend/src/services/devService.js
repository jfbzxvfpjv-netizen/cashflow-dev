/**
 * Servicio Axios para el módulo de desarrollo (reset y fixtures).
 * Incluye el endpoint de información del entorno.
 */
import api from './api'

export default {
  /** Obtiene el entorno actual (development/production). */
  getEnv() {
    return api.get('/system/env')
  },

  /** Reset de datos: borra transacciones conservando catálogos. */
  resetData() {
    return api.post('/dev/reset-data', { confirm: 'RESET' })
  },

  /** Reset completo: borra todo y re-ejecuta seed. */
  resetFull() {
    return api.post('/dev/reset-full', { confirm: 'RESET' })
  },

  /**
   * Carga un fixture de datos de prueba.
   * @param {string} nombre - 'basico', 'completo' o 'importacion'
   */
  loadFixture(nombre) {
    return api.post(`/dev/load-fixture/${nombre}`, { confirm: 'LOAD' })
  }
}
