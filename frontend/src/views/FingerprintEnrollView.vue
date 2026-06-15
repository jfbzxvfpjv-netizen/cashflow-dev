<template>
  <div class="max-w-5xl mx-auto px-4 py-6">
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-800">Enrolar Huellas</h1>
        <p class="text-sm text-gray-500 mt-1">
          Empleados de tu delegación · coloca el dedo del empleado en el lector para registrar su huella
        </p>
      </div>
      <div class="flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium" :class="engineBadgeClasses">
        <span class="w-2 h-2 rounded-full" :class="engineDotClasses"></span>
        <span>{{ engineLabel }}</span>
      </div>
    </div>

    <div v-if="statusMessage"
         :class="[
           'mb-4 px-4 py-3 rounded-lg text-sm',
           statusType === 'success' ? 'bg-green-50 text-green-800 border border-green-200' :
           statusType === 'error' ? 'bg-red-50 text-red-800 border border-red-200' :
           'bg-blue-50 text-blue-800 border border-blue-200'
         ]">
      {{ statusMessage }}
    </div>

    <div class="flex items-center gap-3 mb-4">
      <input v-model="filterName" type="text" placeholder="Buscar por nombre..."
             class="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none" />
      <button @click="refresh" :disabled="loading"
              class="p-2 text-gray-600 hover:bg-gray-100 rounded-lg disabled:opacity-50 transition-colors" title="Recargar listado">
        <svg class="w-5 h-5" :class="{ 'animate-spin': loading }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
        </svg>
      </button>
    </div>

    <div class="bg-white rounded-lg shadow overflow-hidden">
      <div v-if="loading" class="p-8 text-center text-gray-500">Cargando empleados...</div>

      <div v-else-if="filteredEmployees.length === 0" class="p-8 text-center text-gray-500">
        {{ employees.length === 0 ? 'No hay empleados en tu delegación.' : 'Ningún empleado coincide con el filtro.' }}
      </div>

      <table v-else class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <th class="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Empleado</th>
            <th class="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Delegación</th>
            <th class="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase tracking-wider">Capturas</th>
            <th class="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Dedos enrolados</th>
            <th class="px-4 py-3 text-center text-xs font-semibold text-gray-600 uppercase tracking-wider">Enrolar</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-100">
          <tr v-for="emp in filteredEmployees" :key="emp.employee_id" class="hover:bg-gray-50 transition-colors">
            <td class="px-4 py-3"><span class="text-sm font-medium text-gray-800">{{ emp.full_name }}</span></td>
            <td class="px-4 py-3"><span class="text-sm text-gray-600">{{ emp.delegacion || '—' }}</span></td>
            <td class="px-4 py-3 text-right">
              <span class="text-sm font-mono" :class="emp.capture_count > 0 ? 'text-gray-800' : 'text-gray-400'">{{ emp.capture_count }}</span>
            </td>
            <td class="px-4 py-3">
              <div v-if="emp.fingers_enrolled && emp.fingers_enrolled.length > 0" class="flex flex-wrap gap-1">
                <span v-for="finger in emp.fingers_enrolled" :key="finger"
                      class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-blue-50 text-blue-700 border border-blue-200">
                  {{ fingerLabel(finger) }}
                </span>
              </div>
              <span v-else class="text-sm text-gray-400 italic">Sin enrolment</span>
            </td>
            <td class="px-4 py-3">
              <div class="flex items-center justify-center">
                <button @click="openEnroll(emp)" class="p-1.5 text-blue-600 hover:bg-blue-50 rounded-md transition-colors" title="Enrolar nuevo dedo">
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
                  </svg>
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>

      <div v-if="filteredEmployees.length > 0" class="px-4 py-2 bg-gray-50 text-xs text-gray-500 text-right">
        {{ filteredEmployees.length }} empleado{{ filteredEmployees.length !== 1 ? 's' : '' }}
      </div>
    </div>

    <FingerprintEnrollDialog
      v-if="enrollModalOpen && enrollTargetEmp"
      :employee-id="enrollTargetEmp.employee_id"
      :employee-name="enrollTargetEmp.full_name"
      :existing-fingers="enrollTargetEmp.fingers_enrolled || []"
      @close="closeEnroll"
      @enrolled="onEnrolled"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '@/services/api'
import FingerprintEnrollDialog from '@/components/admin/FingerprintEnrollDialog.vue'

const employees = ref([])
const engineStatus = ref(null)
const loading = ref(true)
const loadingEngine = ref(true)
const filterName = ref('')
const statusMessage = ref('')
const statusType = ref('info')
const enrollModalOpen = ref(false)
const enrollTargetEmp = ref(null)

const API_BASE = '/fingerprints'

const FINGER_LABELS = {
  right_thumb: 'Pulgar D', right_index: 'Índice D', right_middle: 'Medio D', right_ring: 'Anular D', right_pinky: 'Meñique D',
  left_thumb: 'Pulgar I', left_index: 'Índice I', left_middle: 'Medio I', left_ring: 'Anular I', left_pinky: 'Meñique I',
}

async function loadEmployees() {
  loading.value = true
  try {
    const { data } = await api.get(`${API_BASE}/employees`)
    employees.value = Array.isArray(data) ? data : (data.employees || data.items || [])
  } catch (err) {
    showStatus(err.response?.data?.detail || 'Error al cargar el listado de empleados', 'error')
    employees.value = []
  } finally {
    loading.value = false
  }
}

async function loadEngineStatus() {
  loadingEngine.value = true
  try {
    const { data } = await api.get(`${API_BASE}/engine/status`)
    engineStatus.value = data
  } catch (err) {
    engineStatus.value = { healthy: false, error: 'No se pudo consultar el estado del motor' }
  } finally {
    loadingEngine.value = false
  }
}

function refresh() { loadEngineStatus(); loadEmployees() }

const filteredEmployees = computed(() => {
  return employees.value.filter(emp => {
    if (filterName.value) {
      const needle = filterName.value.toLowerCase()
      if (!(emp.full_name || '').toLowerCase().includes(needle)) return false
    }
    return true
  })
})

const engineBadgeClasses = computed(() => {
  if (loadingEngine.value) return 'bg-gray-100 text-gray-600'
  if (engineStatus.value?.healthy) return 'bg-green-50 text-green-700 border border-green-200'
  return 'bg-red-50 text-red-700 border border-red-200'
})
const engineDotClasses = computed(() => {
  if (loadingEngine.value) return 'bg-gray-400 animate-pulse'
  if (engineStatus.value?.healthy) return 'bg-green-500'
  return 'bg-red-500'
})
const engineLabel = computed(() => {
  if (loadingEngine.value) return 'Comprobando motor...'
  if (engineStatus.value?.healthy) {
    const v = engineStatus.value?.version
    return v ? `Motor activo · ${v}` : 'Motor activo'
  }
  return engineStatus.value?.error || 'Motor caído'
})

function openEnroll(emp) { enrollTargetEmp.value = emp; enrollModalOpen.value = true }
function closeEnroll() { enrollModalOpen.value = false; enrollTargetEmp.value = null }
function onEnrolled({ employee_id, finger_position }) {
  showStatus(`Huella ${fingerLabel(finger_position)} enrolada para empleado #${employee_id}`, 'success')
  loadEmployees()
}
function fingerLabel(code) { return FINGER_LABELS[code] || code }
function showStatus(message, type = 'info') {
  statusMessage.value = message; statusType.value = type
  if (type === 'success') setTimeout(clearStatus, 8000)
}
function clearStatus() { statusMessage.value = '' }

onMounted(() => { loadEngineStatus(); loadEmployees() })
</script>
