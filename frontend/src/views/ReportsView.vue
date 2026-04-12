<template>
  <div class="max-w-4xl mx-auto px-4 py-6">
    <h1 class="text-2xl font-bold text-gray-800 mb-6">Informes</h1>

    <!-- Informe de cierre de sesión -->
    <div class="bg-white rounded-xl shadow p-6 mb-6">
      <h2 class="text-lg font-semibold text-gray-700 mb-4">Informe de cierre de sesión</h2>
      <p class="text-sm text-gray-500 mb-4">
        Selecciona una sesión de caja cerrada para descargar su informe completo con el
        detalle de todas las transacciones, totales de ingresos y egresos, y la diferencia final.
      </p>
      <div class="flex flex-wrap items-end gap-4">
        <div class="flex-1 min-w-[200px]">
          <label class="block text-xs text-gray-500 mb-1">Sesión</label>
          <select v-model="sessionId"
            class="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500">
            <option value="">Seleccionar sesión...</option>
            <option v-for="s in sessions" :key="s.id" :value="s.id">
              #{{ s.id }} — {{ s.delegacion }} — {{ formatFecha(s.opened_at) }}
              {{ s.status === 'closed' ? '(Cerrada)' : '(Abierta)' }}
            </option>
          </select>
        </div>
        <div class="flex gap-2">
          <button @click="downloadSession('pdf')" :disabled="!sessionId"
            class="px-4 py-2 bg-red-600 text-white rounded-lg text-sm font-medium hover:bg-red-700 disabled:opacity-50 transition">
            📄 PDF
          </button>
          <button @click="downloadSession('xlsx')" :disabled="!sessionId"
            class="px-4 py-2 bg-green-600 text-white rounded-lg text-sm font-medium hover:bg-green-700 disabled:opacity-50 transition">
            📥 Excel
          </button>
        </div>
      </div>
    </div>

    <!-- Informe de período libre -->
    <div class="bg-white rounded-xl shadow p-6">
      <h2 class="text-lg font-semibold text-gray-700 mb-4">Informe de período</h2>
      <p class="text-sm text-gray-500 mb-4">
        Define un rango de fechas y, opcionalmente, filtra por delegación y categoría
        para generar un informe detallado del período seleccionado.
      </p>
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
        <div>
          <label class="block text-xs text-gray-500 mb-1">Fecha inicio</label>
          <input type="date" v-model="periodStart"
            class="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500" />
        </div>
        <div>
          <label class="block text-xs text-gray-500 mb-1">Fecha fin</label>
          <input type="date" v-model="periodEnd"
            class="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500" />
        </div>
        <div>
          <label class="block text-xs text-gray-500 mb-1">Delegación (opcional)</label>
          <select v-model="periodDelegacion"
            class="w-full border rounded-lg px-3 py-2 text-sm">
            <option value="">Todas</option>
            <option value="Bata">Bata</option>
            <option value="Malabo">Malabo</option>
          </select>
        </div>
        <div>
          <label class="block text-xs text-gray-500 mb-1">Categoría (opcional)</label>
          <select v-model="periodCategory"
            class="w-full border rounded-lg px-3 py-2 text-sm">
            <option value="">Todas</option>
            <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.name }}</option>
          </select>
        </div>
      </div>
      <div class="flex gap-2">
        <button @click="downloadPeriod('pdf')" :disabled="!periodStart || !periodEnd"
          class="px-4 py-2 bg-red-600 text-white rounded-lg text-sm font-medium hover:bg-red-700 disabled:opacity-50 transition">
          📄 PDF
        </button>
        <button @click="downloadPeriod('xlsx')" :disabled="!periodStart || !periodEnd"
          class="px-4 py-2 bg-green-600 text-white rounded-lg text-sm font-medium hover:bg-green-700 disabled:opacity-50 transition">
          📥 Excel
        </button>
      </div>
    </div>

    <!-- Feedback de descarga -->
    <div v-if="downloading" class="fixed bottom-6 right-6 bg-blue-600 text-white px-5 py-3 rounded-xl shadow-lg text-sm flex items-center gap-2">
      <svg class="animate-spin h-4 w-4" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg>
      Generando informe...
    </div>
    <div v-if="error" class="fixed bottom-6 right-6 bg-red-600 text-white px-5 py-3 rounded-xl shadow-lg text-sm">
      {{ error }}
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import reportService from '@/services/reportService'
import api from '@/services/api'

const auth = useAuthStore()

const sessions = ref([])
const categories = ref([])
const sessionId = ref('')
const periodStart = ref('')
const periodEnd = ref('')
const periodDelegacion = ref('')
const periodCategory = ref('')
const downloading = ref(false)
const error = ref('')

function formatFecha(iso) {
  if (!iso) return ''
  return new Date(iso).toLocaleDateString('es-ES', { day:'2-digit', month:'2-digit', year:'numeric' })
}

async function loadSessions() {
  try {
    const res = await api.get('/sessions', { params: { } })
    sessions.value = (res.data.items || res.data || []).sort((a, b) => b.id - a.id)
  } catch (e) {
    console.error('Error cargando sesiones:', e)
  }
}

async function loadCategories() {
  try {
    const res = await api.get('/categories')
    categories.value = res.data || []
  } catch (e) {
    console.error('Error cargando categorías:', e)
  }
}

async function downloadSession(format) {
  if (!sessionId.value) return
  downloading.value = true
  error.value = ''
  try {
    await reportService.downloadSessionReport(sessionId.value, format)
  } catch (e) {
    error.value = 'Error al generar el informe de sesión'
    setTimeout(() => error.value = '', 4000)
  } finally {
    downloading.value = false
  }
}

async function downloadPeriod(format) {
  if (!periodStart.value || !periodEnd.value) return
  downloading.value = true
  error.value = ''
  try {
    const params = {
      date_start: periodStart.value,
      date_end: periodEnd.value,
      format
    }
    if (periodDelegacion.value) params.delegacion = periodDelegacion.value
    if (periodCategory.value) params.category_id = periodCategory.value
    await reportService.downloadPeriodReport(params)
  } catch (e) {
    error.value = 'Error al generar el informe de período'
    setTimeout(() => error.value = '', 4000)
  } finally {
    downloading.value = false
  }
}

onMounted(() => {
  loadSessions()
  loadCategories()
})
</script>
