<!-- M10b — Detalle de periodo de nómina con pago individual + firma -->
<template>
  <div class="p-4 max-w-6xl mx-auto">
    <div class="mb-3">
      <router-link to="/payrolls" class="text-blue-600 hover:underline text-sm">← Volver a nóminas</router-link>
    </div>

    <div v-if="period" class="mb-4">
      <div class="flex justify-between items-start mb-3">
        <div>
          <h1 class="text-xl font-bold">{{ monthNames[period.month - 1] }} {{ period.year }} — {{ period.delegacion }}</h1>
          <div class="text-sm text-gray-500 mt-1">
            <span :class="period.status === 'paid' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'"
                  class="px-2 py-0.5 rounded text-xs font-medium mr-2">
              {{ period.status === 'paid' ? 'Pagado' : 'Borrador' }}
            </span>
            Creado por {{ period.created_by_name }} el {{ new Date(period.created_at).toLocaleDateString('es-ES') }}
            <span v-if="period.paid_at"> · Cerrado el {{ new Date(period.paid_at).toLocaleDateString('es-ES') }}</span>
          </div>
        </div>
        <div class="flex gap-2">
          <button v-if="canClose" @click="doClose" :disabled="busy"
                  class="bg-green-600 hover:bg-green-700 text-white px-3 py-1.5 rounded text-sm disabled:opacity-50">
            Cerrar periodo
          </button>
        </div>
      </div>

      <!-- Resumen -->
      <div class="grid grid-cols-4 gap-3 mb-4">
        <div class="bg-white rounded shadow p-3">
          <div class="text-xs text-gray-500">Empleados</div>
          <div class="text-xl font-bold">{{ period.total_employees }}</div>
        </div>
        <div class="bg-white rounded shadow p-3">
          <div class="text-xs text-gray-500">Total efectivo</div>
          <div class="text-xl font-bold font-mono">{{ Number(period.total_cash).toLocaleString() }} XAF</div>
        </div>
        <div class="bg-white rounded shadow p-3">
          <div class="text-xs text-gray-500">Pagados</div>
          <div class="text-xl font-bold text-green-700">{{ period.paid_count }}</div>
        </div>
        <div class="bg-white rounded shadow p-3">
          <div class="text-xs text-gray-500">Pendientes (con cash)</div>
          <div class="text-xl font-bold text-orange-600">{{ period.pending_count }}</div>
        </div>
      </div>
    </div>

    <!-- Aviso si no es gestor -->
    <div v-if="!isGestor && period?.status === 'draft' && period?.pending_count > 0"
         class="bg-blue-50 border border-blue-200 rounded p-3 mb-3 text-sm text-blue-700">
      Los pagos individuales con firma del empleado solo pueden ejecutarse desde el rol <strong>gestor</strong>.
      Inicia sesión como gestor de {{ period.delegacion }} para procesar las nóminas.
    </div>

    <!-- Entries -->
    <div class="bg-white rounded shadow overflow-x-auto">
      <table class="w-full text-sm">
        <thead class="bg-gray-50">
          <tr>
            <th class="px-3 py-2 text-left">Empleado</th>
            <th class="px-3 py-2 text-right">Bruto</th>
            <th class="px-3 py-2 text-right">Transferencia</th>
            <th class="px-3 py-2 text-right">Efectivo</th>
            <th class="px-3 py-2 text-left">Estado</th>
            <th class="px-3 py-2"></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="e in entries" :key="e.id" class="border-t">
            <td class="px-3 py-2">{{ e.employee_name }}</td>
            <td class="px-3 py-2 text-right font-mono">{{ Number(e.salary_gross).toLocaleString() }}</td>
            <td class="px-3 py-2 text-right font-mono text-gray-500">{{ Number(e.salary_transfer).toLocaleString() }}</td>
            <td class="px-3 py-2 text-right font-mono font-semibold">{{ Number(e.cash_amount).toLocaleString() }}</td>
            <td class="px-3 py-2">
              <span v-if="!e.transaction_id && Number(e.cash_amount) === 0" class="text-gray-400 text-xs">
                Sin efectivo (todo por banco)
              </span>
              <span v-else-if="!e.transaction_id" class="text-orange-600 text-xs">Pendiente</span>
              <span v-else-if="e.transaction_status === 'approved'" class="text-green-700 text-xs">
                Pagado · {{ e.transaction_reference }}
              </span>
              <span v-else-if="e.transaction_status === 'pending_approval'" class="text-yellow-700 text-xs">
                Espera aprobación · {{ e.transaction_reference }}
              </span>
              <span v-else-if="e.transaction_status === 'rejected'" class="text-red-700 text-xs">
                Rechazado · {{ e.transaction_reference }}
              </span>
            </td>
            <td class="px-3 py-2 text-right">
              <button v-if="canPayEntry(e)" @click="openPayModal(e)"
                      class="px-2 py-1 bg-orange-500 hover:bg-orange-600 text-white text-xs rounded">
                Pagar
              </button>
              <button v-else-if="canEditEntry(e)" @click="openEditEntry(e)"
                      class="text-blue-600 hover:underline text-xs ml-2">
                Editar
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Modal Editar entry (admin solo en draft) -->
    <div v-if="editTarget" class="fixed inset-0 bg-black/40 flex items-center justify-center z-50" @click.self="editTarget=null">
      <div class="bg-white rounded p-6 w-full max-w-md">
        <h2 class="text-lg font-semibold mb-1">Editar nómina</h2>
        <p class="text-sm text-gray-600 mb-3">{{ editTarget.employee_name }}</p>
        <div v-if="editErr" class="text-sm text-red-600 mb-2 p-2 bg-red-50 rounded">{{ editErr }}</div>
        <div class="space-y-3">
          <div>
            <label class="block text-xs font-medium text-gray-700 mb-1">Efectivo (XAF) *</label>
            <input v-model.number="editForm.cash_amount" type="number" min="0"
                   class="w-full border rounded px-2 py-1.5 text-sm font-mono" />
          </div>
          <div>
            <label class="block text-xs font-medium text-gray-700 mb-1">Notas</label>
            <textarea v-model="editForm.notes" @blur="editForm.notes = normalizeText(editForm.notes)" rows="2" class="w-full border rounded px-2 py-1.5 text-sm"></textarea>
          </div>
        </div>
        <div class="flex justify-end gap-2 mt-4">
          <button @click="editTarget=null" class="px-4 py-1.5 text-sm rounded border">Cancelar</button>
          <button @click="doSaveEntry" :disabled="busy"
                  class="px-4 py-1.5 text-sm rounded bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50">
            Guardar
          </button>
        </div>
      </div>
    </div>

    <!-- Modal Pagar entry con firma -->
    <div v-if="payTarget" class="fixed inset-0 bg-black/40 flex items-start justify-center z-50 overflow-auto p-4" @click.self="closePayModal">
      <div class="bg-white rounded p-6 w-full max-w-lg my-4">
        <h2 class="text-lg font-semibold mb-1">Pagar nómina</h2>
        <p class="text-sm text-gray-600 mb-2">{{ payTarget.employee_name }}</p>
        <div class="bg-gray-50 rounded p-3 mb-3 text-sm">
          <div class="flex justify-between"><span class="text-gray-500">Importe a pagar en efectivo:</span>
            <span class="font-mono font-semibold">{{ Number(payTarget.cash_amount).toLocaleString() }} XAF</span></div>
          <div class="flex justify-between"><span class="text-gray-500">Periodo:</span>
            <span>{{ monthNames[period.month - 1] }} {{ period.year }}</span></div>
        </div>
        <div v-if="payErr" class="text-sm text-red-600 mb-2 p-2 bg-red-50 rounded">{{ payErr }}</div>

        <!-- Componente firma -->
        <div class="mb-3">
          <label class="block text-xs font-semibold text-gray-700 mb-2">Firma del empleado *</label>
          <SignatureSection
            contraparte-type="employee"
            :contraparte-id="payTarget.employee_id"
            @signature-ready="onSignatureReady" />
        </div>

        <div class="flex justify-end gap-2 mt-4">
          <button @click="closePayModal" :disabled="busy" class="px-4 py-1.5 text-sm rounded border">Cancelar</button>
          <button @click="doPay" :disabled="busy || !signaturePayload"
                  class="px-4 py-1.5 text-sm rounded bg-orange-500 text-white hover:bg-orange-600 disabled:opacity-50">
            {{ busy ? 'Pagando…' : 'Confirmar pago' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import payrollService from '@/services/payrollService'
import { useAuthStore } from '@/stores/auth'
import { normalizeText } from '@/composables/useTextNormalizer'
import SignatureSection from '@/components/admin/SignatureSection.vue'

const route = useRoute()
const auth = useAuthStore()
const isAdmin = computed(() => auth.user?.role === 'admin')
const isGestor = computed(() => auth.user?.role === 'gestor')

const period = ref(null)
const entries = ref([])
const busy = ref(false)
const editTarget = ref(null)
const editForm = ref({ cash_amount: 0, notes: '' })
const editErr = ref('')
const payTarget = ref(null)
const payErr = ref('')
const signaturePayload = ref(null)

const monthNames = ['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre']

const canClose = computed(() =>
  isAdmin.value && period.value && period.value.status === 'draft' && period.value.pending_count === 0
)
function canEditEntry(e) {
  return isAdmin.value && period.value?.status === 'draft' && !e.transaction_id
}
function canPayEntry(e) {
  return isGestor.value
    && period.value?.status === 'draft'
    && !e.transaction_id
    && Number(e.cash_amount) > 0
    && auth.user?.delegacion === period.value.delegacion
}

async function load() {
  const r = await payrollService.getPeriod(route.params.id)
  period.value = r.data
  entries.value = r.data.entries || []
}

function openEditEntry(e) {
  editTarget.value = e
  editForm.value = { cash_amount: Number(e.cash_amount), notes: e.notes || '' }
  editErr.value = ''
}

async function doSaveEntry() {
  busy.value = true
  try {
    await payrollService.updateEntry(period.value.id, editTarget.value.id, {
      cash_amount: editForm.value.cash_amount,
      notes: editForm.value.notes || null,
    })
    editTarget.value = null
    await load()
  } catch (e) {
    editErr.value = e.response?.data?.detail || 'Error al guardar'
  } finally {
    busy.value = false
  }
}

function openPayModal(e) {
  payTarget.value = e
  payErr.value = ''
  signaturePayload.value = null
}
function closePayModal() {
  payTarget.value = null
  signaturePayload.value = null
  payErr.value = ''
}
function onSignatureReady(payload) {
  signaturePayload.value = payload
}

async function doPay() {
  if (!signaturePayload.value) {
    payErr.value = 'Captura la firma del empleado antes de confirmar'
    return
  }
  // Construir signature como espera el backend (signer_type + datos según método)
  const sp = signaturePayload.value
  const isFp = sp.signature_method === 'fingerprint'
  const signature = {
    signer_type: 'employee',
    signer_name: sp.signer_name,
    signature_method: sp.signature_method,
    employee_id: sp.employee_id,
    supplier_id: null,
    partner_id: null,
  }
  if (isFp) {
    signature.fingerprint_score = Math.round(Number(sp.fingerprint_score) || 0)
    signature.fingerprint_finger_position = sp.fingerprint_finger_position
    signature.fingerprint_attempts = sp.fingerprint_attempts
  } else {
    // wacom o wacom_provisional
    signature.signature_data = (sp.wacom_image_b64 || '').replace(/^data:image\/[a-z]+;base64,/, '')
    signature.fingerprint_failed_scores = sp.fingerprint_failed_scores || null
  }

  busy.value = true
  payErr.value = ''
  try {
    await payrollService.payEntry(period.value.id, payTarget.value.id, signature)
    closePayModal()
    await load()
  } catch (e) {
    payErr.value = e.response?.data?.detail || 'Error al pagar'
  } finally {
    busy.value = false
  }
}

async function doClose() {
  if (!confirm('¿Cerrar este periodo? No se podrán añadir más pagos después.')) return
  busy.value = true
  try {
    await payrollService.closePeriod(period.value.id)
    await load()
  } catch (e) {
    alert(e.response?.data?.detail || 'Error al cerrar')
  } finally {
    busy.value = false
  }
}

onMounted(load)
</script>
