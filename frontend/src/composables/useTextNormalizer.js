/**
 * Normalizador de texto unificado (Sentence case estricto).
 *
 * Reglas por palabra:
 *  - Si SOLO contiene letras: pasarla a lowercase salvo que sea una sigla
 *    corta (todo mayúsculas con length <= 4): "DHL" se preserva, "AGENTE"
 *    o "veHIculo" se normaliza a "agente"/"vehiculo".
 *  - Si contiene números o guiones/puntos (matrículas, códigos, referencias):
 *    preservarla tal cual ("WN-192-AM" se mantiene).
 *
 * Reglas globales:
 *  - trim + colapsar espacios múltiples a uno
 *  - Primera letra del resultado siempre mayúscula
 */
function normalizeWord(word) {
  if (!word) return word
  const onlyLetters = /^[a-zA-ZÁÉÍÓÚÑÜáéíóúñü]+$/.test(word)
  if (onlyLetters) {
    const isAllCaps = word === word.toUpperCase()
    if (isAllCaps && word.length <= 4) return word  // Sigla corta: DHL, IBM, MTN
    return word.toLowerCase()
  }
  return word  // Matrícula, código, número
}

export function normalizeText(text) {
  if (text === null || text === undefined) return text
  let t = String(text).trim().replace(/\s+/g, ' ')
  if (!t) return ''
  const words = t.split(' ').map(normalizeWord)
  let result = words.join(' ')
  return result.charAt(0).toUpperCase() + result.slice(1)
}
