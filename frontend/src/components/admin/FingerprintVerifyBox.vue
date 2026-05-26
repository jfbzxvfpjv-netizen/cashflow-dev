<template>
  <div class="bg-white border border-gray-200 rounded-lg p-4 shadow-sm">
    <!-- Cabecera con nombre y contador -->
    <div class="text-sm mb-3 flex items-center justify-between">
      <div>
        <span class="text-gray-600">Verificacion biometrica de</span>
        <strong class="ml-1 text-gray-800">{{ signerName || ('Empleado #' + employeeId) }}</strong>
      </div>
      <div v-if="!verified && !fallbackTriggered" class="text-xs text-gray-500">
        Intento {{ attempts.length + 1 }} de {{ maxAttempts }}
      </div>
    </div>

    <!-- Icono y mensaje de estado -->
    <div class="flex flex-col items-center mb-3">
      <div class="w-20 h-20 rounded-full flex items-center justify-center transition-colors mb-2"
           :class="iconBgClass">
        <span class="text-4xl">{{ iconEmoji }}</span>
      </div>
      <p class="text-center text-sm font-medium" :class="messageColorClass">
        {{ statusMessage }}
      </p>
    </div>

    <!-- Resultado del ultimo verify -->
    <div v-if="lastVerifyResult" class="mb-3">
      <div :class="lastVerifyResult.matched
              ? 'bg-green-50 border border-green-200 text-green-800'
              : 'bg-amber-50 border border-amber-200 text-amber-800'"
           class="rounded p-3 text-sm">
        <div class="flex justify-between items-center">
          <div>
            <strong v-if="lastVerifyResult.matched">Coincidencia confirmada</strong>
            <strong v-else>No coincide</strong>
            <span v-if="lastVerifyResult.finger_position" class="ml-2 text-xs">
              ({{ fingerLabel(lastVerifyResult.finger_position) }})
            </span>
          </div>
          <div class="font-mono text-xs">
            Score {{ Math.round(lastVerifyResult.score) }} / Threshold {{ lastVerifyResult.threshold }}
          </div>
        </div>
      </div>
    </div>

    <!-- Historico de intentos fallidos -->
    <div v-if="attempts.length > 0 && !verified" class="mb-3 bg-gray-50 rounded p-2 text-xs">
      <div class="text-gray-600 mb-1">Intentos previos:</div>
      <div class="flex gap-1 flex-wrap">
        <span v-for="(a, i) in attempts" :key="i"
              class="inline-flex items-center px-2 py-0.5 rounded-full bg-red-100 text-red-700">
          #{{ i + 1 }}: score {{ Math.round(a.score) }}
        </span>
      </div>
    </div>

    <!-- Boton accion -->
    <div class="flex justify-center gap-2">
      <button v-if="!verified && !fallbackTriggered"
              @click="startVerification"
              :disabled="state === 'capturing' || verifying"
              :class="[
                'px-4 py-2 text-sm rounded transition-colors font-medium',
                (state === 'capturing' || verifying)
                  ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                  : 'bg-indigo-600 hover:bg-indigo-700 text-white'
              ]">
        {{ attempts.length === 0 ? 'Iniciar verificacion' : 'Reintentar' }}
      </button>
      <button v-if="verified"
              @click="reverify"
              class="px-4 py-2 text-sm rounded transition-colors font-medium bg-indigo-600 hover:bg-indigo-700 text-white">
        Re-verificar (descartar y volver a empezar)
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import api from '../../services/api'
import { useFingerprintCapture } from '../../composables/useFingerprintCapture'

const props = defineProps({
  employeeId: { type: Number, required: true },
  signerName: { type: String, default: '' },
  maxAttempts: { type: Number, default: 3 },
})

const emit = defineEmits(['verified', 'fallback-required', 'reset'])

const {
  state, lastSample, error: captureError, deviceConnected,
  connect, startCapture, stopCapture, disconnect,
} = useFingerprintCapture({ autoQualityCheck: false })

const verifying = ref(false)
const lastVerifyResult = ref(null)
const attempts = ref([])
const verified = ref(false)
const fallbackTriggered = ref(false)
const internalError = ref(null)

const FINGER_LABELS = {
  right_thumb: 'Pulgar D', right_index: 'Indice D', right_middle: 'Corazon D',
  right_ring: 'Anular D', right_pinky: 'Menique D',
  left_thumb: 'Pulgar I', left_index: 'Indice I', left_middle: 'Corazon I',
  left_ring: 'Anular I', left_pinky: 'Menique I',
}

function fingerLabel(code) { return FINGER_LABELS[code] || code }

const statusMessage = computed(() => {
  if (internalError.value) return internalError.value
  if (verified.value) return '✓ Identidad verificada'
  if (fallbackTriggered.value) return `${props.maxAttempts} intentos fallidos. Cambiando a firma Wacom...`
  if (verifying.value) return 'Verificando contra plantillas enroladas...'
  if (state.value === 'capturing') return 'Coloca el dedo en el sensor'
  if (state.value === 'sample_received') return 'Muestra recibida'
  if (state.value === 'connected') return 'Listo. Pulsa "Iniciar verificacion"'
  if (state.value === 'connecting' || state.value === 'idle' || state.value === 'disconnected') return 'Conectando lector...'
  if (state.value === 'error') return captureError.value || 'Error con el lector'
  return ''
})

const messageColorClass = computed(() => {
  if (verified.value) return 'text-green-700'
  if (fallbackTriggered.value) return 'text-red-700'
  if (state.value === 'error' || internalError.value) return 'text-red-600'
  if (state.value === 'capturing') return 'text-blue-700'
  return 'text-gray-700'
})

const iconBgClass = computed(() => {
  if (verified.value) return 'bg-green-100'
  if (fallbackTriggered.value) return 'bg-red-100'
  if (state.value === 'error' || internalError.value) return 'bg-red-100'
  if (state.value === 'capturing') return 'bg-blue-100 animate-pulse'
  return 'bg-gray-100'
})

const iconEmoji = computed(() => {
  if (verified.value) return '✓'
  if (fallbackTriggered.value) return '⚠'
  if (state.value === 'error' || internalError.value) return '✗'
  return '👆'
})

async function reverify() {
  // Resetear estado interno para volver a empezar la verificacion
  verified.value = false
  lastVerifyResult.value = null
  attempts.value = []
  internalError.value = null
  emit('reset')
  try {
    if (!deviceConnected.value) await connect()
    await startCapture()
  } catch (err) {
    internalError.value = err.message || 'Error reiniciando captura'
  }
}

async function startVerification() {
  internalError.value = null
  lastVerifyResult.value = null
  // Reset del composable para preparar nueva captura limpia
  try { await stopCapture() } catch (_) {}
  lastSample.value = null
  if (deviceConnected.value) {
    state.value = 'connected'
  }
  try {
    if (!deviceConnected.value) {
      state.value = 'connecting'
      await connect()
    }
    await startCapture()
  } catch (err) {
    internalError.value = err.message || 'Error iniciando captura'
  }
}

watch(state, async (newState) => {
  if (newState !== 'sample_received') return
  if (!lastSample.value || verifying.value || verified.value || fallbackTriggered.value) return

  verifying.value = true
  try {
    const { data } = await api.post('/fingerprints/verify', {
      employee_id: props.employeeId,
      image_b64: lastSample.value,
    })
    lastVerifyResult.value = data
    if (data.matched) {
      verified.value = true
      emit('verified', {
        employee_id: props.employeeId,
        score: data.score,
        finger_position: data.finger_position,
        attempts: attempts.value.length + 1,
      })
      try { await stopCapture() } catch (_) {}
    } else {
      attempts.value.push({
        score: data.score,
        finger_position: data.finger_position,
      })
      if (attempts.value.length >= props.maxAttempts) {
        // Fallback final tras agotar intentos
        fallbackTriggered.value = true
        emit('fallback-required', {
          employee_id: props.employeeId,
          failed_scores: attempts.value.map(a => a.score),
        })
        try { await stopCapture() } catch (_) {}
        try { await disconnect() } catch (_) {}
      } else {
        // Fallo no final: dejar el lector listo para que el boton Reintentar
        // pueda lanzar una nueva captura sin que el composable se quede colgado
        try { await stopCapture() } catch (_) {}
        lastSample.value = null
        if (deviceConnected.value) {
          state.value = 'connected'
        }
      }
    }
  } catch (err) {
    internalError.value = err.response?.data?.detail || err.message || 'Error verificando'
  } finally {
    verifying.value = false
  }
})

onMounted(async () => {
  try {
    await connect()
  } catch (err) {
    internalError.value = err.message || 'Error conectando lector'
  }
})

onBeforeUnmount(async () => {
  try { await stopCapture() } catch (_) {}
  try { await disconnect() } catch (_) {}
})
</script>
