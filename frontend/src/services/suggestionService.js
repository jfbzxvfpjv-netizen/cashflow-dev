// Servicio S10 — Sugerencias de categorización
// Llama al endpoint GET /suggestions/transaction-categorization del backend.
// Documentación: pliego_s10_sugerencias_categorizacion_v1.md

import api from './api'

/**
 * Solicita una sugerencia de categoría/subcategoría según el contexto del formulario.
 *
 * @param {Object} ctx
 * @param {string|null} ctx.concept            — texto del concepto
 * @param {number|null} ctx.supplier_id        — FK proveedor (excluyente)
 * @param {number|null} ctx.employee_id        — FK empleado (excluyente)
 * @param {number|null} ctx.partner_id         — FK socio (excluyente)
 * @param {string|null} ctx.counterparty_free  — contraparte texto libre (si no hay FK)
 * @param {number|null} ctx.project_id         — proyecto seleccionado
 * @param {string|null} ctx.delegacion         — Bata | Malabo (admin/contable)
 *
 * @returns {Promise<Object|null>} Objeto con la sugerencia o null si silencio (nivel 5).
 *   Estructura del objeto:
 *     {
 *       category_id, subcategory_id, category_name, subcategory_name,
 *       confidence: 'high' | 'medium' | 'medium-low',
 *       source_level: 1..4,
 *       sample_count: number,
 *       scope: 'counterparty' | 'project' | 'global'
 *     }
 *
 * El backend siempre devuelve HTTP 200 con campos en null cuando no hay sugerencia
 * (nivel 5 silencio). Aquí lo normalizamos a null para simplificar el consumo.
 */
async function fetch(ctx) {
  // Limpieza: pasar solo parámetros con valor (evita ?supplier_id=null en la URL)
  const params = {}
  if (ctx.concept && ctx.concept.trim().length > 0) params.concept = ctx.concept.trim()
  if (ctx.supplier_id) params.supplier_id = ctx.supplier_id
  if (ctx.employee_id) params.employee_id = ctx.employee_id
  if (ctx.partner_id) params.partner_id = ctx.partner_id
  if (ctx.counterparty_free && ctx.counterparty_free.trim().length > 0) {
    params.counterparty_free = ctx.counterparty_free.trim()
  }
  if (ctx.project_id) params.project_id = ctx.project_id
  if (ctx.delegacion) params.delegacion = ctx.delegacion

  // Si no hay ni concepto ni contraparte, no llamamos al backend (devolvería 400)
  const hasConcept = !!params.concept
  const hasCounterparty = !!(params.supplier_id || params.employee_id ||
                             params.partner_id || params.counterparty_free)
  if (!hasConcept && !hasCounterparty) return null

  try {
    const { data } = await api.get('/suggestions/transaction-categorization', { params })
    // Nivel 5 (silencio) — el backend devuelve campos null pero source_level=5
    if (!data || data.source_level === 5 || !data.category_id) return null
    return data
  } catch (e) {
    // No bloqueamos el flujo del formulario si el endpoint falla
    console.warn('[suggestionService] error al obtener sugerencia', e)
    return null
  }
}

export default { fetch }
