<template>
  <div class="bg-white border border-gray-200 rounded-lg p-4 shadow-sm">
    <div v-if="label" class="text-xs font-semibold text-gray-600 uppercase tracking-wider mb-3 text-center">
      {{ label }}
    </div>

    <!-- Icono grande con color segun estado -->
    <div class="flex justify-center mb-3">
      <div
        class="w-20 h-20 rounded-full flex items-center justify-center transition-colors"
        :class="iconBgClass"
      >
        <span class="text-4xl">{{ iconEmoji }}</span>
      </div>
    </div>

    <!-- Mensaje de estado -->
    <p class="text-center text-sm mb-3 min-h-[2.5em]" :class="messageColorClass">
      {{ statusMessage }}
    </p>

    <!-- Metricas: quality y minutiae cuando hay muestra -->
    <div v-if="lastQuality !== null" class="grid grid-cols-2 gap-2 text-center text-xs mb-3">
      <div class="bg-gray-50 rounded p-2">
        <div class="text-gray-500">Calidad</div>
        <div class="font-mono font-semibold text-lg" :class="qualityColorClass">
          {{ lastQuality }}
        </div>
      </div>
      <div class="bg-gray-50 rounded p-2">
        <div class="text-gray-500">Minutiae</div>
        <div class="font-mono font-semibold text-lg">{{ lastMinutiae }}</div>
      </div>
    </div>

    <!-- Botones segun estado -->
    <div class="flex justify-center gap-2">
      <button
        v-if="showRetry"
        @click="handleRetry"
        class="px-3 py-1.5 text-sm bg-amber-100 hover:bg-amber-200 text-amber-800 rounded transition-colors font-medium"
      >
        Reintentar
      </button>
      <button
        v-if="showAccept"
        @click="handleAccept"
        class="px-3 py-1.5 text-sm bg-green-600 hover:bg-green-700 text-white rounded transition-colors font-medium"
      >
        Aceptar captura
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, onBeforeUnmount, watch } from 'vue'
import { useFingerprintCapture } from '../../composables/useFingerprintCapture'

const props = defineProps({
  label: { type: String, default: '' },
  autoStart: { type: Boolean, default: true },
  minQuality: { type: Number, default: 50 },
})

const emit = defineEmits(['captured', 'failed', 'state-change'])

const {
  state, lastSample, lastQuality, lastMinutiae, error, deviceConnected,
  connect, startCapture, stopCapture, disconnect,
} = useFingerprintCapture({ autoQualityCheck: true })

const statusMessage = computed(() => {
  switch (state.value) {
    case 'idle':
    case 'disconnected':
      return 'Conectando lector...'
    case 'connecting':
      return 'Conectando lector...'
    case 'connected':
      return 'Listo. Coloca el dedo en el sensor.'
    case 'capturing':
      return 'Coloca el dedo en el sensor'
    case 'sample_received':
      return lastQuality.value >= props.minQuality
        ? 'Captura aceptable'
        : 'Calidad insuficiente, reintenta con mejor presion'
    case 'error':
      return error.value || 'Error inesperado'
    default:
      return state.value
  }
})

const messageColorClass = computed(() => {
  if (state.value === 'error') return 'text-red-600 font-medium'
  if (state.value === 'sample_received') {
    return lastQuality.value >= props.minQuality
      ? 'text-green-700 font-medium'
      : 'text-amber-700 font-medium'
  }
  return 'text-gray-600'
})

const iconBgClass = computed(() => {
  if (state.value === 'error') return 'bg-red-100'
  if (state.value === 'sample_received') {
    return lastQuality.value >= props.minQuality ? 'bg-green-100' : 'bg-amber-100'
  }
  if (state.value === 'capturing') return 'bg-blue-100 animate-pulse'
  if (state.value === 'connected') return 'bg-gray-100'
  return 'bg-gray-50'
})

const iconEmoji = computed(() => {
  if (state.value === 'error') return '✗'
  if (state.value === 'sample_received') {
    return lastQuality.value >= props.minQuality ? '✓' : '↻'
  }
  return '👆'
})

const qualityColorClass = computed(() => {
  const q = lastQuality.value
  if (q === null) return 'text-gray-600'
  if (q >= 70) return 'text-green-700'
  if (q >= props.minQuality) return 'text-green-600'
  return 'text-amber-600'
})

const showRetry = computed(() => {
  return state.value === 'sample_received' && lastQuality.value < props.minQuality
})

const showAccept = computed(() => {
  return state.value === 'sample_received' && lastQuality.value >= props.minQuality
})

watch(state, (newState) => {
  emit('state-change', newState)
})

function handleAccept() {
  emit('captured', {
    imageB64: lastSample.value,
    quality: lastQuality.value,
    minutiae: lastMinutiae.value,
  })
}

async function handleRetry() {
  try { await stopCapture() } catch (_) {}
  lastSample.value = null
  lastQuality.value = null
  lastMinutiae.value = null
  error.value = null
  state.value = deviceConnected.value ? 'connected' : 'idle'
  try {
    if (!deviceConnected.value) await connect()
    await startCapture()
  } catch (err) {
    console.warn('[FingerprintCaptureBox] reintento fallo:', err)
    emit('failed', err.message || 'Error reintentando')
  }
}

onMounted(async () => {
  try {
    await connect()
    if (props.autoStart) await startCapture()
  } catch (err) {
    console.warn('[FingerprintCaptureBox] connect/start fallo:', err)
    emit('failed', err.message || 'Error al iniciar el lector')
  }
})

onBeforeUnmount(async () => {
  try { await stopCapture() } catch (_) {}
  try { await disconnect() } catch (_) {}
})
</script>
