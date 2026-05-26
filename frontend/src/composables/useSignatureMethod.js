/**
 * useSignatureMethod
 *
 * Wrapper sobre el endpoint GET /api/v1/fingerprints/signature-method.
 * Resuelve que metodo de firma aplica para una contraparte dada.
 *
 * Contraparte types soportados (alineados con backend):
 *   - 'supplier'  -> siempre wacom
 *   - 'employee'  -> fingerprint si tiene enrolment, sino wacom_only_no_enrollment
 *   - 'partner'   -> siempre wacom
 *   - 'free'      -> siempre wacom (texto libre)
 *
 * Response shape:
 *   {
 *     method: 'wacom' | 'fingerprint' | 'wacom_only_no_enrollment',
 *     signer_name: string,
 *     employee_id: number | null,
 *     has_enrollment: boolean,
 *     fallback_method: 'wacom' | null,  // solo cuando method='fingerprint'
 *   }
 */
import { ref } from 'vue'
import api from '../services/api'

export function useSignatureMethod() {
  const method = ref(null)
  const signerName = ref('')
  const employeeId = ref(null)
  const hasEnrollment = ref(false)
  const fallbackMethod = ref(null)
  const loading = ref(false)
  const error = ref(null)

  async function resolve(contraparteType, contraparteId) {
    method.value = null
    error.value = null
    loading.value = true
    try {
      const params = { contraparte_type: contraparteType }
      if (contraparteId !== null && contraparteId !== undefined) {
        params.contraparte_id = contraparteId
      }
      const { data } = await api.get('/fingerprints/signature-method', { params })
      method.value = data.method
      signerName.value = data.signer_name
      employeeId.value = data.employee_id
      hasEnrollment.value = !!data.has_enrollment
      fallbackMethod.value = data.fallback_method
      return data
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || 'Error resolviendo metodo de firma'
      throw err
    } finally {
      loading.value = false
    }
  }

  function reset() {
    method.value = null
    signerName.value = ''
    employeeId.value = null
    hasEnrollment.value = false
    fallbackMethod.value = null
    error.value = null
  }

  return {
    method,
    signerName,
    employeeId,
    hasEnrollment,
    fallbackMethod,
    loading,
    error,
    resolve,
    reset,
  }
}
