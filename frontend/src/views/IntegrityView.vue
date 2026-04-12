<!--
  Módulo 6 — IntegrityView.vue
  Panel de verificación SHA-256. Compara el hash almacenado de cada transacción
  con el hash recalculado para detectar manipulaciones directas en la BD.
-->
<template>
  <div class="p-4 max-w-3xl mx-auto">
    <h1 class="text-xl font-bold mb-4">Verificación de Integridad SHA-256</h1>

    <div class="bg-white rounded shadow p-4">
      <p class="text-sm text-gray-600 mb-4">
        Compara el hash almacenado de cada transacción con el hash recalculado en tiempo real
        para detectar posibles manipulaciones directas en la base de datos.
      </p>

      <button @click="verify" :disabled="loading"
              class="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 text-sm disabled:opacity-50">
        {{ loading ? 'Verificando...' : 'Ejecutar verificación completa' }}
      </button>

      <div v-if="result" class="mt-4 space-y-3">
        <div class="grid grid-cols-3 gap-3 text-center">
          <div class="bg-blue-50 rounded p-3">
            <div class="text-2xl font-bold">{{ result.total }}</div>
            <div class="text-xs text-gray-500">Total</div>
          </div>
          <div class="bg-green-50 rounded p-3">
            <div class="text-2xl font-bold text-green-600">{{ result.verified_ok }}</div>
            <div class="text-xs text-gray-500">Correctas</div>
          </div>
          <div :class="result.failures.length ? 'bg-red-50' : 'bg-green-50'" class="rounded p-3">
            <div class="text-2xl font-bold" :class="result.failures.length ? 'text-red-600' : 'text-green-600'">
              {{ result.failures.length }}
            </div>
            <div class="text-xs text-gray-500">Inconsistencias</div>
          </div>
        </div>

        <div v-if="result.failures.length === 0"
             class="bg-green-100 text-green-700 p-3 rounded text-sm font-medium text-center">
          ✓ Todas las transacciones verificadas correctamente
        </div>

        <div v-else class="bg-red-100 p-3 rounded">
          <p class="text-red-700 font-medium text-sm mb-2">⚠ Se detectaron inconsistencias:</p>
          <table class="w-full text-xs">
            <thead>
              <tr><th class="text-left px-2 py-1">Ref.</th><th class="text-left px-2 py-1">Hash almacenado</th><th class="text-left px-2 py-1">Hash calculado</th></tr>
            </thead>
            <tbody>
              <tr v-for="f in result.failures" :key="f.id" class="border-t">
                <td class="px-2 py-1 font-mono">{{ f.reference }}</td>
                <td class="px-2 py-1 font-mono break-all">{{ f.stored_hash?.substring(0, 16) }}...</td>
                <td class="px-2 py-1 font-mono break-all">{{ f.computed_hash?.substring(0, 16) }}...</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import transactionService from '@/services/transactionService'

const loading = ref(false)
const result = ref(null)

async function verify() {
  loading.value = true
  result.value = null
  try {
    const { data } = await transactionService.verifyAll()
    result.value = data
  } finally {
    loading.value = false
  }
}
</script>
