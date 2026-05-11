<template>
  <div class="max-w-6xl mx-auto px-4 py-6">
    <!-- Cabecera -->
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-gray-800">
        F2 — Test composable useFingerprintCapture
      </h1>
      <p class="text-sm text-gray-500 mt-1">
        Pagina de desarrollo eliminable al cerrar la fase. Para validar el
        composable contra el lector real o con muestras simuladas sin hardware.
      </p>
    </div>

    <!-- Estado actual -->
    <div class="bg-white rounded-lg shadow p-4 mb-4">
      <h2 class="text-sm font-semibold text-gray-700 uppercase tracking-wider mb-3">
        Estado actual
      </h2>
      <dl class="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
        <div>
          <dt class="text-gray-500 text-xs">Estado</dt>
          <dd class="font-mono font-medium" :class="stateColorClass">{{ state }}</dd>
        </div>
        <div>
          <dt class="text-gray-500 text-xs">Lector</dt>
          <dd class="font-mono font-medium"
              :class="deviceConnected ? 'text-green-700' : 'text-gray-400'">
            {{ deviceConnected ? 'Conectado' : 'No detectado' }}
          </dd>
        </div>
        <div>
          <dt class="text-gray-500 text-xs">Calidad</dt>
          <dd class="font-mono font-medium">{{ lastQuality !== null ? lastQuality : '—' }}</dd>
        </div>
        <div>
          <dt class="text-gray-500 text-xs">Minutiae</dt>
          <dd class="font-mono font-medium">{{ lastMinutiae !== null ? lastMinutiae : '—' }}</dd>
        </div>
      </dl>
      <div v-if="error"
           class="mt-3 px-3 py-2 bg-red-50 border border-red-200 rounded-md text-sm text-red-700">
        <span class="font-semibold">Error:</span> {{ error }}
      </div>
    </div>

    <!-- Acciones contra lector real -->
    <div class="bg-white rounded-lg shadow p-4 mb-4">
      <h2 class="text-sm font-semibold text-gray-700 uppercase tracking-wider mb-3">
        Lector real
      </h2>
      <div class="flex flex-wrap gap-2">
        <button @click="connect"
                :disabled="['connecting', 'connected', 'capturing', 'sample_received'].includes(state)"
                class="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium
                       hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed
                       transition-colors">
          Connect
        </button>
        <button @click="disconnect"
                :disabled="['idle', 'disconnected'].includes(state)"
                class="px-4 py-2 bg-gray-600 text-white rounded-lg text-sm font-medium
                       hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed
                       transition-colors">
          Disconnect
        </button>
        <button @click="startCapture"
                :disabled="state !== 'connected'"
                class="px-4 py-2 bg-green-600 text-white rounded-lg text-sm font-medium
                       hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed
                       transition-colors">
          Start capture
        </button>
        <button @click="stopCapture"
                :disabled="state !== 'capturing'"
                class="px-4 py-2 bg-amber-600 text-white rounded-lg text-sm font-medium
                       hover:bg-amber-700 disabled:opacity-50 disabled:cursor-not-allowed
                       transition-colors">
          Stop capture
        </button>
      </div>
    </div>

    <!-- Simulacion sin hardware -->
    <div class="bg-white rounded-lg shadow p-4 mb-4">
      <h2 class="text-sm font-semibold text-gray-700 uppercase tracking-wider mb-3">
        Simulacion de muestra
      </h2>
      <p class="text-xs text-gray-500 mb-2">
        Inyecta una imagen PNG en base64 sin pasar por el lector. Util para
        verificar la llamada automatica a /fingerprints/quality.
      </p>
      <textarea v-model="customB64"
                rows="3"
                placeholder="Pega aqui base64 de una imagen PNG (sin prefijo data:image/png;base64,)..."
                class="w-full px-3 py-2 border border-gray-300 rounded-lg
                       text-xs font-mono focus:ring-2 focus:ring-blue-500
                       focus:border-blue-500 outline-none"></textarea>
      <div class="flex flex-wrap gap-2 mt-2">
        <button @click="simulateSample(customB64)"
                :disabled="!customB64"
                class="px-4 py-2 bg-purple-600 text-white rounded-lg text-sm font-medium
                       hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed
                       transition-colors">
          Simular con base64 pegado
        </button>
        <button @click="injectDummyPng"
                class="px-4 py-2 bg-purple-100 text-purple-700 rounded-lg text-sm font-medium
                       hover:bg-purple-200 transition-colors border border-purple-300">
          Inyectar PNG 1x1 dummy
        </button>
      </div>
    </div>

    <!-- Preview muestra recibida -->
    <div v-if="lastSample" class="bg-white rounded-lg shadow p-4">
      <h2 class="text-sm font-semibold text-gray-700 uppercase tracking-wider mb-3">
        Ultima muestra recibida
      </h2>
      <div class="flex items-start gap-4 flex-wrap">
        <div class="flex-shrink-0 p-2 bg-gray-100 rounded-lg">
          <img :src="`data:image/png;base64,${lastSample}`"
               alt="Muestra de huella"
               class="max-w-xs max-h-64 border border-gray-300 rounded bg-white" />
        </div>
        <div class="flex-1 text-xs text-gray-500 min-w-0">
          <p class="font-semibold mb-1 text-gray-700">Base64 (primeros 200 chars):</p>
          <code class="block bg-gray-50 p-2 rounded font-mono break-all">{{ lastSample.slice(0, 200) }}{{ lastSample.length > 200 ? '...' : '' }}</code>
          <p class="mt-2">Tamano total: {{ lastSample.length }} caracteres base64</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useFingerprintCapture } from '@/composables/useFingerprintCapture'

const {
  state, lastSample, lastQuality, lastMinutiae, error, deviceConnected,
  connect, disconnect, startCapture, stopCapture, simulateSample,
} = useFingerprintCapture()

const customB64 = ref('')

// PNG 1x1 transparente en base64
const DUMMY_PNG_1X1 = 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=='

function injectDummyPng() {
  simulateSample(DUMMY_PNG_1X1)
}

const stateColorClass = computed(() => {
  switch (state.value) {
    case 'idle':
    case 'disconnected':
      return 'text-gray-500'
    case 'connecting':
      return 'text-blue-600'
    case 'connected':
      return 'text-green-600'
    case 'capturing':
      return 'text-amber-600'
    case 'sample_received':
      return 'text-purple-600'
    case 'error':
      return 'text-red-600'
    default:
      return 'text-gray-700'
  }
})
</script>
