<template>
  <div>
    <!-- Loading inicial -->
    <div v-if="loading"
         class="bg-white border border-gray-200 rounded-lg p-6 text-center text-gray-500">
      <div class="text-2xl mb-2 animate-pulse">⏳</div>
      Resolviendo metodo de firma...
    </div>

    <!-- Error de resolucion -->
    <div v-else-if="resolveError"
         class="bg-red-50 border border-red-200 rounded-lg p-4 text-sm text-red-700">
      <strong>Error:</strong> {{ resolveError }}
    </div>

    <!-- Vias polimorficas segun el metodo efectivo -->
    <FingerprintVerifyBox v-else-if="effectiveMethod === 'fingerprint'"
                          :employee-id="employeeId"
                          :signer-name="signerName"
                          @verified="onFingerprintVerified"
                          @fallback-required="onFingerprintFallback"
                          @reset="onChildReset" />

    <WacomSTU430Capture v-else-if="effectiveMethod === 'wacom_only_no_enrollment' || effectiveMethod === 'wacom_provisional'"
                     :signer-name="signerName"
                     :provisional="true"
                     @signed="onWacomSigned"
                     @reset="onChildReset" />

    <WacomSTU430Capture v-else-if="effectiveMethod === 'wacom'"
                     :signer-name="signerName"
                     :provisional="false"
                     @signed="onWacomSigned"
                     @reset="onChildReset" />

    <!-- Confirmacion visual cuando la firma esta lista -->
    <div v-if="signatureCaptured"
         class="mt-3 bg-green-50 border border-green-200 rounded-lg p-3 text-sm text-green-700 font-medium text-center">
      ✓ Firma capturada — metodo:
      <span class="font-mono ml-1">{{ signatureCaptured.signature_method }}</span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useSignatureMethod } from '../../composables/useSignatureMethod'
import WacomCaptureBox from './WacomCaptureBox.vue'
import WacomSTU430Capture from './WacomSTU430Capture.vue'
import FingerprintVerifyBox from './FingerprintVerifyBox.vue'

const props = defineProps({
  contraparteType: { type: String, required: true },
  contraparteId: { type: Number, default: null },
})

const emit = defineEmits(['signature-ready'])

const {
  method, signerName, employeeId, loading, error: resolveError, resolve, reset,
} = useSignatureMethod()

// Estado interno del orquestador
const fallbackFromFingerprint = ref(false)
const fingerprintFailedScores = ref(null)
const signatureCaptured = ref(null)

/**
 * Metodo efectivo: si hubo fallback de huella tras 3 fallos, forzamos
 * el path wacom_provisional. Si no, usamos lo que dijo el backend.
 */
const effectiveMethod = computed(() => {
  if (fallbackFromFingerprint.value) return 'wacom_provisional'
  return method.value
})

async function resolveCounterparty() {
  signatureCaptured.value = null
  fallbackFromFingerprint.value = false
  fingerprintFailedScores.value = null
  reset()
  if (!props.contraparteType) return
  try {
    await resolve(props.contraparteType, props.contraparteId)
  } catch (_) {
    // El composable ya guarda error.value; se renderiza en el template
  }
}

function onFingerprintVerified({ score, finger_position, attempts }) {
  const payload = {
    signature_method: 'fingerprint',
    employee_id: employeeId.value,
    signer_name: signerName.value,
    wacom_image_b64: null,
    fingerprint_score: score,
    fingerprint_finger_position: finger_position,
    fingerprint_attempts: attempts,
    fingerprint_failed_scores: null,
  }
  signatureCaptured.value = payload
  emit('signature-ready', payload)
}

function onFingerprintFallback({ failed_scores }) {
  fingerprintFailedScores.value = failed_scores
  fallbackFromFingerprint.value = true
}

function onChildReset() {
  // El hijo (WacomCaptureBox o FingerprintVerifyBox) ha sido reseteado por el usuario.
  // Limpiamos el banner verde y el payload local. NO emitimos al padre porque el padre
  // solo necesita saber cuando hay una firma nueva (signature-ready).
  signatureCaptured.value = null
  fallbackFromFingerprint.value = false
  fingerprintFailedScores.value = null
}

function onWacomSigned({ imageB64, provisional }) {
  // wacom_provisional aplica si:
  //   a) el empleado no tiene enrolment (method == wacom_only_no_enrollment)
  //   b) hubo fallback desde fingerprint tras 3 fallos
  const isProvisional = provisional || fallbackFromFingerprint.value
  const payload = {
    signature_method: isProvisional ? 'wacom_provisional' : 'wacom',
    employee_id: employeeId.value,
    signer_name: signerName.value,
    wacom_image_b64: imageB64,
    fingerprint_score: null,
    fingerprint_finger_position: null,
    fingerprint_attempts: null,
    fingerprint_failed_scores: fingerprintFailedScores.value,
  }
  signatureCaptured.value = payload
  emit('signature-ready', payload)
}

watch([() => props.contraparteType, () => props.contraparteId], () => {
  resolveCounterparty()
})

onMounted(() => {
  resolveCounterparty()
})
</script>
