<template>
  <div class="container mx-auto px-4 py-6 max-w-4xl">
    <h1 class="text-2xl font-bold mb-2">F4 — Test SignatureSection polimorfico</h1>
    <p class="text-sm text-gray-600 mb-6">
      Pagina de desarrollo eliminable al cerrar F5. Permite probar los cuatro caminos
      del dispatcher de firma segun el tipo de contraparte y el estado de enrolment del empleado.
    </p>

    <!-- Selector de tipo de contraparte -->
    <div class="bg-white border border-gray-200 rounded-lg p-4 mb-4 shadow-sm">
      <h2 class="text-sm font-semibold text-gray-700 uppercase tracking-wider mb-3">
        1. Tipo de contraparte
      </h2>
      <div class="grid grid-cols-4 gap-2">
        <button v-for="t in TYPES" :key="t"
                @click="selectType(t)"
                :class="[
                  'p-3 rounded-lg border-2 transition-colors text-sm font-medium capitalize',
                  contraparteType === t
                    ? 'bg-indigo-50 border-indigo-500 text-indigo-700'
                    : 'bg-white border-gray-300 hover:border-indigo-300 text-gray-700'
                ]">
          {{ t }}
        </button>
      </div>
      <p class="text-xs text-gray-500 mt-2">
        supplier/partner/free → Wacom siempre · employee con enrolment → fingerprint · employee sin enrolment → wacom provisional
      </p>
    </div>

    <!-- Selector de id segun tipo -->
    <div v-if="contraparteType && contraparteType !== 'free'"
         class="bg-white border border-gray-200 rounded-lg p-4 mb-4 shadow-sm">
      <h2 class="text-sm font-semibold text-gray-700 uppercase tracking-wider mb-3">
        2. ID de {{ contraparteType }}
      </h2>

      <div v-if="contraparteType === 'employee'">
        <div v-if="loadingEmployees" class="text-sm text-gray-500">Cargando empleados...</div>
        <div v-else class="space-y-1 max-h-80 overflow-y-auto">
          <button v-for="emp in employees" :key="emp.employee_id"
                  @click="contraparteId = emp.employee_id"
                  :class="[
                    'w-full text-left p-2 rounded border transition-colors text-sm',
                    contraparteId === emp.employee_id
                      ? 'bg-indigo-50 border-indigo-500'
                      : 'bg-white border-gray-200 hover:border-indigo-300'
                  ]">
            <div class="flex justify-between items-center">
              <span class="font-medium">{{ emp.full_name }} <span class="text-gray-500 text-xs">({{ emp.delegacion }})</span></span>
              <span v-if="emp.fingers_enrolled && emp.fingers_enrolled.length > 0"
                    class="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded">
                Con enrolment ({{ emp.fingers_enrolled.length }})
              </span>
              <span v-else class="text-xs bg-gray-100 text-gray-500 px-2 py-0.5 rounded">
                Sin enrolment
              </span>
            </div>
          </button>
        </div>
      </div>

      <div v-else>
        <input v-model.number="contraparteId" type="number" placeholder="ID numerico"
               class="w-full px-3 py-2 border border-gray-300 rounded text-sm" />
        <p class="text-xs text-gray-500 mt-1">
          Para {{ contraparteType }} el dispatcher devuelve siempre Wacom; el ID solo se usa
          para resolver el nombre del firmante.
        </p>
      </div>
    </div>

    <!-- SignatureSection (solo cuando hay tipo + id valido) -->
    <div v-if="contraparteType && (contraparteType === 'free' || contraparteId !== null)"
         class="mb-4">
      <h2 class="text-sm font-semibold text-gray-700 uppercase tracking-wider mb-3">
        3. Captura de firma
      </h2>
      <SignatureSection :contraparte-type="contraparteType"
                        :contraparte-id="contraparteId"
                        @signature-ready="onSignatureReady" />
    </div>

    <!-- Payload final emitido -->
    <div v-if="lastPayload"
         class="bg-white border border-gray-200 rounded-lg p-4 shadow-sm">
      <h2 class="text-sm font-semibold text-gray-700 uppercase tracking-wider mb-3">
        4. Payload emitido (signature-ready)
      </h2>
      <pre class="text-xs bg-gray-50 p-3 rounded overflow-x-auto font-mono">{{ payloadFormatted }}</pre>
      <p class="text-xs text-gray-500 mt-2">
        Este es el payload que F5 va a inyectar en el POST /transactions junto al resto del body.
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import api from '@/services/api'
import SignatureSection from '@/components/admin/SignatureSection.vue'

const TYPES = ['supplier', 'employee', 'partner', 'free']

const contraparteType = ref(null)
const contraparteId = ref(null)
const employees = ref([])
const loadingEmployees = ref(false)
const lastPayload = ref(null)

const payloadFormatted = computed(() => {
  if (!lastPayload.value) return ''
  // Truncar campos largos para visualizacion
  const p = { ...lastPayload.value }
  if (p.wacom_image_b64 && p.wacom_image_b64.length > 80) {
    p.wacom_image_b64 = p.wacom_image_b64.slice(0, 80) + '... (' + lastPayload.value.wacom_image_b64.length + ' chars total)'
  }
  return JSON.stringify(p, null, 2)
})

function selectType(t) {
  contraparteType.value = t
  contraparteId.value = null
  lastPayload.value = null
  if (t === 'employee' && employees.value.length === 0) {
    loadEmployees()
  }
}

async function loadEmployees() {
  loadingEmployees.value = true
  try {
    const { data } = await api.get('/fingerprints/employees')
    employees.value = data
  } catch (err) {
    console.error('[AdminSignatureTest] Error cargando empleados:', err)
  } finally {
    loadingEmployees.value = false
  }
}

function onSignatureReady(payload) {
  lastPayload.value = payload
}
</script>
