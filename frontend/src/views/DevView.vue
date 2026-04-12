<template>
  <div class="max-w-3xl mx-auto p-6">
    <h1 class="text-2xl font-bold mb-6">🔧 Panel de Desarrollo</h1>

    <div v-if="!isDev" class="bg-gray-100 rounded p-6 text-center text-gray-500">
      Este panel solo está disponible en el entorno de desarrollo.
    </div>

    <div v-else>
      <!-- Reset de datos -->
      <div class="bg-red-50 border-2 border-red-300 rounded-lg p-6 mb-6">
        <h2 class="text-lg font-semibold text-red-800 mb-2">Reset de datos</h2>
        <p class="text-sm text-red-700 mb-4">
          Borra transacciones, sesiones, adjuntos, firmas y aprobaciones.
          Conserva catálogos, usuarios y configuración del sistema.
        </p>
        <div class="flex items-end gap-4">
          <div class="flex-1">
            <label class="block text-sm font-medium text-red-700 mb-1">
              Escriba RESET para confirmar
            </label>
            <input v-model="confirmData" type="text" placeholder="RESET"
                   class="w-full border-red-300 border rounded px-3 py-2" />
          </div>
          <button @click="doResetData" :disabled="confirmData !== 'RESET' || loading"
                  class="bg-red-600 text-white px-6 py-2 rounded hover:bg-red-700 disabled:opacity-50">
            {{ loading ? 'Ejecutando...' : 'Reset datos' }}
          </button>
        </div>
      </div>

      <!-- Reset completo -->
      <div class="bg-red-100 border-2 border-red-400 rounded-lg p-6 mb-6">
        <h2 class="text-lg font-semibold text-red-900 mb-2">Reset completo</h2>
        <p class="text-sm text-red-800 mb-4">
          Borra TODA la base de datos y re-ejecuta el seed completo.
          Incluye catálogos, usuarios y configuración.
        </p>
        <div class="flex items-end gap-4">
          <div class="flex-1">
            <label class="block text-sm font-medium text-red-800 mb-1">
              Escriba RESET para confirmar
            </label>
            <input v-model="confirmFull" type="text" placeholder="RESET"
                   class="w-full border-red-400 border rounded px-3 py-2" />
          </div>
          <button @click="doResetFull" :disabled="confirmFull !== 'RESET' || loading"
                  class="bg-red-800 text-white px-6 py-2 rounded hover:bg-red-900 disabled:opacity-50">
            {{ loading ? 'Ejecutando...' : 'Reset completo' }}
          </button>
        </div>
      </div>

      <!-- Cargar fixture -->
      <div class="bg-yellow-50 border-2 border-yellow-300 rounded-lg p-6 mb-6">
        <h2 class="text-lg font-semibold text-yellow-800 mb-2">Cargar fixture de prueba</h2>
        <p class="text-sm text-yellow-700 mb-4">
          Carga un conjunto de datos de prueba predefinido (primero ejecuta reset de datos).
        </p>
        <div class="flex items-end gap-4">
          <div>
            <label class="block text-sm font-medium text-yellow-700 mb-1">Tipo de fixture</label>
            <select v-model="fixtureName" class="border-yellow-300 border rounded px-3 py-2">
              <option value="basico">Básico (10 transacciones)</option>
              <option value="completo">Completo (50 transacciones)</option>
              <option value="importacion">Importación (20 registros importados)</option>
            </select>
          </div>
          <button @click="doLoadFixture" :disabled="loading"
                  class="bg-yellow-600 text-white px-6 py-2 rounded hover:bg-yellow-700 disabled:opacity-50">
            {{ loading ? 'Cargando...' : 'Cargar fixture' }}
          </button>
        </div>
      </div>

      <!-- Resultado -->
      <div v-if="result" class="bg-white border rounded-lg p-6">
        <h3 class="font-semibold mb-2">Resultado</h3>
        <p class="text-green-700">{{ result.message }}</p>
        <pre v-if="result.details && Object.keys(result.details).length"
             class="mt-2 text-xs bg-gray-100 p-3 rounded overflow-auto">{{ JSON.stringify(result.details, null, 2) }}</pre>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import devService from '@/services/devService'

const isDev = ref(false)
const loading = ref(false)
const confirmData = ref('')
const confirmFull = ref('')
const fixtureName = ref('basico')
const result = ref(null)

async function checkEnv() {
  try {
    const { data } = await devService.getEnv()
    isDev.value = data.env === 'development'
  } catch { isDev.value = false }
}

async function doResetData() {
  loading.value = true
  result.value = null
  try {
    const { data } = await devService.resetData()
    result.value = data
    confirmData.value = ''
  } catch (err) {
    alert('Error: ' + (err.response?.data?.detail || err.message))
  } finally { loading.value = false }
}

async function doResetFull() {
  loading.value = true
  result.value = null
  try {
    const { data } = await devService.resetFull()
    result.value = data
    confirmFull.value = ''
  } catch (err) {
    alert('Error: ' + (err.response?.data?.detail || err.message))
  } finally { loading.value = false }
}

async function doLoadFixture() {
  loading.value = true
  result.value = null
  try {
    const { data } = await devService.loadFixture(fixtureName.value)
    result.value = data
  } catch (err) {
    alert('Error: ' + (err.response?.data?.detail || err.message))
  } finally { loading.value = false }
}

onMounted(() => { checkEnv() })
</script>
