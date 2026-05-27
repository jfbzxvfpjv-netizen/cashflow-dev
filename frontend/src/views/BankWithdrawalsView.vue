<template>
  <div class="p-6 max-w-7xl mx-auto">
    <!-- Cabecera -->
    <div class="flex items-center justify-between mb-4">
      <div>
        <h1 class="text-2xl font-semibold text-gray-900">Retiradas bancarias</h1>
        <p class="text-sm text-gray-500 mt-1">
          Flujo: gestor solicita → contable formaliza con cheque → admin aprueba → gestor confirma recepción
        </p>
      </div>
      <button
        :disabled="!canRequest"
        :title="canRequest ? '' : 'Solo el gestor puede solicitar retiradas bancarias'"
        :class="canRequest ? 'bg-blue-600 hover:bg-blue-700 text-white' : 'bg-gray-300 text-gray-500 cursor-not-allowed'"
        class="px-4 py-2 text-sm rounded-md"
        @click="openRequestModal"
      >
        + Nueva solicitud
      </button>
    </div>

    <!-- Filtros -->
    <div class="bg-white rounded-md shadow-sm border border-gray-200 p-4 mb-4 flex flex-wrap gap-3">
      <select v-model="f.delegacion" @change="load" class="border rounded px-3 py-1.5 text-sm">
        <option value="">Todas las delegaciones</option>
        <option value="Bata">Bata</option>
        <option value="Malabo">Malabo</option>
      </select>
      <select v-model="f.status" @change="load" class="border rounded px-3 py-1.5 text-sm">
        <option value="">Todos los estados</option>
        <option value="requested">Solicitada</option>
        <option value="formalized">Formalizada</option>
        <option value="approved">Aprobada</option>
        <option value="confirmed">Confirmada</option>
        <option value="rejected">Rechazada</option>
      </select>
      <input type="date" v-model="f.ds" @change="load" class="border rounded px-3 py-1.5 text-sm" />
      <input type="date" v-model="f.de" @change="load" class="border rounded px-3 py-1.5 text-sm" />
    </div>

    <!-- Listado -->
    <div v-if="items.length === 0" class="text-center text-gray-400 py-12 bg-white rounded border border-dashed">
      No hay retiradas que mostrar.
    </div>
    <div v-else class="space-y-3">
      <div v-for="w in items" :key="w.id"
           :class="['bg-white rounded-md border-l-4 shadow-sm p-4', bc(w.status)]">
        <!-- Línea 1: estado, delegación, importe -->
        <div class="flex justify-between items-start mb-2">
          <div class="flex items-center gap-3">
            <span :class="['px-2 py-0.5 rounded text-xs font-medium', badge(w.status)]">
              {{ label(w.status) }}
            </span>
            <span class="text-sm text-gray-500">{{ w.delegacion }}</span>
            <span class="text-xs text-gray-400">#{{ w.id }}</span>
          </div>
          <div class="text-right">
            <div class="text-xl font-semibold text-gray-900">{{ fmt(w.amount) }} XAF</div>
          </div>
        </div>

        <!-- Línea 2: motivo de la solicitud -->
        <div v-if="w.reason" class="text-sm text-gray-700 mb-2">
          <span class="text-gray-500">Motivo:</span> {{ w.reason }}
        </div>

        <!-- Línea 3: datos bancarios cuando ya está formalizada -->
        <div v-if="w.cheque_reference" class="text-sm text-gray-600 mb-2 flex flex-wrap gap-4">
          <span><span class="text-gray-500">Cuenta:</span> {{ w.account_bank_name }} · {{ w.account_number }}</span>
          <span><span class="text-gray-500">Cheque:</span> {{ w.cheque_reference }}</span>
        </div>

        <!-- Línea 4: trazabilidad de los pasos -->
        <div class="text-xs text-gray-500 grid grid-cols-2 md:grid-cols-4 gap-2 mb-3">
          <div>
            <span class="font-medium">Solicitada</span><br>
            {{ w.requested_by_name || w.proposed_by_name || '—' }}<br>
            <span class="text-gray-400">{{ fmtDt(w.requested_at || w.proposed_at) }}</span>
          </div>
          <div v-if="w.formalized_at">
            <span class="font-medium">Formalizada</span><br>
            {{ w.formalized_by_name }}<br>
            <span class="text-gray-400">{{ fmtDt(w.formalized_at) }}</span>
          </div>
          <div v-if="w.approved_at">
            <span class="font-medium">Aprobada</span><br>
            {{ w.approved_by_name }}<br>
            <span class="text-gray-400">{{ fmtDt(w.approved_at) }}</span>
          </div>
          <div v-if="w.confirmed_at">
            <span class="font-medium">Confirmada</span><br>
            {{ w.confirmed_by_name }}<br>
            <span class="text-gray-400">{{ fmtDt(w.confirmed_at) }}</span>
          </div>
        </div>

        <!-- Motivo de rechazo si aplica -->
        <div v-if="w.status === 'rejected' && w.rejection_reason" class="text-sm text-red-700 bg-red-50 p-2 rounded mb-2">
          <span class="font-medium">Rechazada:</span> {{ w.rejection_reason }}
        </div>

        <!-- Notas internas -->
        <div v-if="w.notes" class="text-xs text-gray-500 italic whitespace-pre-line mb-2">
          {{ w.notes }}
        </div>

        <!-- Botones de acción por estado × rol -->
        <div class="flex gap-2 flex-wrap pt-2 border-t border-gray-100">
          <!-- requested -->
          <button v-if="w.status === 'requested' && canFormalize"
                  @click="openFormalizeModal(w)"
                  class="px-3 py-1.5 text-xs bg-orange-600 hover:bg-orange-700 text-white rounded">
            Formalizar (cuenta + cheque)
          </button>
          <button v-if="w.status === 'requested' && isAdmin"
                  @click="openRejectModal(w)"
                  class="px-3 py-1.5 text-xs bg-red-100 hover:bg-red-200 text-red-700 rounded">
            Rechazar
          </button>
          <button v-if="w.status === 'requested' && canCancel(w)"
                  @click="doCancel(w.id)"
                  class="px-3 py-1.5 text-xs bg-gray-200 hover:bg-gray-300 text-gray-700 rounded">
            Cancelar
          </button>

          <!-- formalized -->
          <button v-if="w.status === 'formalized' && isAdmin"
                  @click="doApprove(w.id)"
                  class="px-3 py-1.5 text-xs bg-blue-600 hover:bg-blue-700 text-white rounded">
            Aprobar
          </button>
          <button v-if="w.status === 'formalized' && isAdmin"
                  @click="openRejectModal(w)"
                  class="px-3 py-1.5 text-xs bg-red-100 hover:bg-red-200 text-red-700 rounded">
            Rechazar
          </button>

          <!-- approved -->
          <button v-if="w.status === 'approved' && canConfirm(w)"
                  @click="doConfirm(w.id)"
                  class="px-3 py-1.5 text-xs bg-green-600 hover:bg-green-700 text-white rounded">
            Confirmar recepción
          </button>
        </div>
      </div>
    </div>

    <!-- Modal SOLICITAR (gestor) -->
    <div v-if="modal === 'request'" class="fixed inset-0 bg-black/40 flex items-center justify-center z-50" @click.self="modal = null">
      <div class="bg-white rounded-md p-6 w-full max-w-md">
        <h2 class="text-lg font-semibold mb-4">Solicitar retirada bancaria</h2>
        <div v-if="merr" class="text-sm text-red-600 mb-3 p-2 bg-red-50 rounded">{{ merr }}</div>
        <div class="space-y-3">
          <div>
            <label class="block text-xs font-medium text-gray-700 mb-1">Delegación</label>
            <select v-model="rf.delegacion" class="w-full border rounded px-3 py-1.5 text-sm">
              <option value="Bata">Bata</option>
              <option value="Malabo">Malabo</option>
            </select>
          </div>
          <div>
            <label class="block text-xs font-medium text-gray-700 mb-1">Importe (XAF)</label>
            <input v-model.number="rf.amount" type="number" step="1" class="w-full border rounded px-3 py-1.5 text-sm" />
          </div>
          <div>
            <label class="block text-xs font-medium text-gray-700 mb-1">Motivo *</label>
            <textarea v-model="rf.reason" rows="2" class="w-full border rounded px-3 py-1.5 text-sm"
                      placeholder="P.ej. Pago a proveedores semana 22"></textarea>
          </div>
          <div>
            <label class="block text-xs font-medium text-gray-700 mb-1">Notas (opcional)</label>
            <textarea v-model="rf.notes" rows="2" class="w-full border rounded px-3 py-1.5 text-sm"></textarea>
          </div>
        </div>
        <div class="flex justify-end gap-2 mt-5">
          <button @click="modal = null" class="px-4 py-1.5 text-sm rounded border">Cancelar</button>
          <button :disabled="busy" @click="doRequest" class="px-4 py-1.5 text-sm rounded bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50">
            {{ busy ? 'Enviando…' : 'Solicitar' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Modal FORMALIZAR (contable) -->
    <div v-if="modal === 'formalize'" class="fixed inset-0 bg-black/40 flex items-center justify-center z-50" @click.self="modal = null">
      <div class="bg-white rounded-md p-6 w-full max-w-md">
        <h2 class="text-lg font-semibold mb-1">Formalizar retirada</h2>
        <p class="text-xs text-gray-500 mb-4">
          Retirada #{{ formalizeTarget?.id }} · {{ formalizeTarget?.delegacion }} · {{ fmt(formalizeTarget?.amount || 0) }} XAF
        </p>
        <div v-if="merr" class="text-sm text-red-600 mb-3 p-2 bg-red-50 rounded">{{ merr }}</div>
        <div class="space-y-3">
          <div>
            <label class="block text-xs font-medium text-gray-700 mb-1">Cuenta corporativa *</label>
            <select v-model="ff.corporate_account_id" class="w-full border rounded px-3 py-1.5 text-sm">
              <option value="">— Seleccionar —</option>
              <option v-for="a in accountsForDelegacion" :key="a.id" :value="a.id">
                {{ a.bank_name }} — {{ a.account_number }}
              </option>
            </select>
          </div>
          <div>
            <label class="block text-xs font-medium text-gray-700 mb-1">Número de cheque *</label>
            <input v-model="ff.cheque_reference" class="w-full border rounded px-3 py-1.5 text-sm" />
          </div>
          <div>
            <label class="block text-xs font-medium text-gray-700 mb-1">Notas (opcional)</label>
            <textarea v-model="ff.notes" rows="2" class="w-full border rounded px-3 py-1.5 text-sm"></textarea>
          </div>
        </div>
        <div class="flex justify-end gap-2 mt-5">
          <button @click="modal = null" class="px-4 py-1.5 text-sm rounded border">Cancelar</button>
          <button :disabled="busy" @click="doFormalize" class="px-4 py-1.5 text-sm rounded bg-orange-600 text-white hover:bg-orange-700 disabled:opacity-50">
            {{ busy ? 'Formalizando…' : 'Formalizar' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Modal RECHAZAR (admin) -->
    <div v-if="modal === 'reject'" class="fixed inset-0 bg-black/40 flex items-center justify-center z-50" @click.self="modal = null">
      <div class="bg-white rounded-md p-6 w-full max-w-md">
        <h2 class="text-lg font-semibold mb-4">Rechazar retirada</h2>
        <p class="text-xs text-gray-500 mb-2">
          Retirada #{{ rejectTarget?.id }} · {{ fmt(rejectTarget?.amount || 0) }} XAF
        </p>
        <div v-if="merr" class="text-sm text-red-600 mb-3 p-2 bg-red-50 rounded">{{ merr }}</div>
        <label class="block text-xs font-medium text-gray-700 mb-1">Motivo *</label>
        <textarea v-model="rejectReason" rows="3" class="w-full border rounded px-3 py-1.5 text-sm"
                  placeholder="Explica brevemente por qué se rechaza"></textarea>
        <div class="flex justify-end gap-2 mt-5">
          <button @click="modal = null" class="px-4 py-1.5 text-sm rounded border">Cancelar</button>
          <button :disabled="busy" @click="doReject" class="px-4 py-1.5 text-sm rounded bg-red-600 text-white hover:bg-red-700 disabled:opacity-50">
            {{ busy ? 'Enviando…' : 'Rechazar' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import bwSvc from '@/services/bankWithdrawalService'
import { corporateAccountsApi } from '@/api/catalogs'

const auth = useAuthStore()
const isAdmin       = computed(() => auth.user?.role === 'admin')
const isGestor      = computed(() => auth.user?.role === 'gestor')
const isContable    = computed(() => auth.user?.role === 'contable')
const canRequest    = computed(() => isGestor.value)
const canFormalize  = computed(() => isContable.value || isAdmin.value)

const items   = ref([])
const accounts = ref([])
const f       = ref({ delegacion:'', status:'', ds:'', de:'' })
const modal   = ref(null)
const merr    = ref('')
const busy    = ref(false)

// Formularios de los tres modales
const rf = ref({ delegacion:'', amount:'', reason:'', notes:'' })
const ff = ref({ corporate_account_id:'', cheque_reference:'', notes:'' })
const formalizeTarget = ref(null)
const rejectTarget    = ref(null)
const rejectReason    = ref('')

const accountsForDelegacion = computed(() =>
  accounts.value.filter(a => a.delegacion === formalizeTarget.value?.delegacion)
)

function canCancel(w) {
  // El gestor solicitante o cualquier admin pueden cancelar mientras esté en 'requested'
  return isAdmin.value || (isGestor.value && w.requested_by === auth.user?.id)
}
function canConfirm(w) {
  // El gestor de la misma delegación o admin pueden confirmar
  return isAdmin.value || (isGestor.value && w.delegacion === auth.user?.delegacion)
}

async function load() {
  const params = {}
  if (f.value.delegacion) params.delegacion = f.value.delegacion
  if (f.value.status) params.status = f.value.status
  if (f.value.ds) params.date_start = f.value.ds
  if (f.value.de) params.date_end = f.value.de
  const r = await bwSvc.list(params)
  items.value = r.data.items || []
}

async function loadAccounts() {
  try {
    const r = await corporateAccountsApi.list({ active_only: true })
    accounts.value = r.data?.items || r.data || []
  } catch (e) {
    accounts.value = []
  }
}

function openRequestModal() {
  rf.value = {
    delegacion: auth.user?.delegacion || 'Bata',
    amount: '',
    reason: '',
    notes: '',
  }
  merr.value = ''
  modal.value = 'request'
}

function openFormalizeModal(w) {
  formalizeTarget.value = w
  ff.value = { corporate_account_id:'', cheque_reference:'', notes:'' }
  merr.value = ''
  modal.value = 'formalize'
}

function openRejectModal(w) {
  rejectTarget.value = w
  rejectReason.value = ''
  merr.value = ''
  modal.value = 'reject'
}

async function doRequest() {
  if (!rf.value.delegacion || !rf.value.amount || !rf.value.reason) {
    merr.value = 'Delegación, importe y motivo son obligatorios'
    return
  }
  if (rf.value.reason.length < 5) {
    merr.value = 'El motivo debe tener al menos 5 caracteres'
    return
  }
  busy.value = true
  try {
    await bwSvc.request(rf.value)
    modal.value = null
    await load()
  } catch (e) {
    merr.value = e.response?.data?.detail || 'Error al solicitar'
  } finally {
    busy.value = false
  }
}

async function doFormalize() {
  if (!ff.value.corporate_account_id || !ff.value.cheque_reference) {
    merr.value = 'Cuenta y número de cheque son obligatorios'
    return
  }
  busy.value = true
  try {
    await bwSvc.formalize(formalizeTarget.value.id, ff.value)
    modal.value = null
    await load()
  } catch (e) {
    merr.value = e.response?.data?.detail || 'Error al formalizar'
  } finally {
    busy.value = false
  }
}

async function doApprove(id) {
  try {
    await bwSvc.approve(id, {})
    await load()
  } catch (e) {
    alert(e.response?.data?.detail || 'Error al aprobar')
  }
}

async function doReject() {
  if (!rejectReason.value || rejectReason.value.length < 5) {
    merr.value = 'El motivo de rechazo debe tener al menos 5 caracteres'
    return
  }
  busy.value = true
  try {
    await bwSvc.reject(rejectTarget.value.id, { rejection_reason: rejectReason.value })
    modal.value = null
    await load()
  } catch (e) {
    merr.value = e.response?.data?.detail || 'Error al rechazar'
  } finally {
    busy.value = false
  }
}

async function doCancel(id) {
  if (!confirm('¿Cancelar esta solicitud?')) return
  try {
    await bwSvc.cancel(id)
    await load()
  } catch (e) {
    alert(e.response?.data?.detail || 'Error al cancelar')
  }
}

async function doConfirm(id) {
  if (!confirm('¿Confirmar recepción física del dinero? Esto generará una entrada de caja.')) return
  try {
    await bwSvc.confirm(id, {})
    await load()
  } catch (e) {
    alert(e.response?.data?.detail || 'Error al confirmar')
  }
}

function fmt(n) {
  return new Intl.NumberFormat('es-GQ').format(n)
}
function fmtDt(d) {
  return d ? new Date(d).toLocaleString('es-GQ', { day:'2-digit', month:'2-digit', year:'numeric', hour:'2-digit', minute:'2-digit' }) : '—'
}
function label(s) {
  return {
    requested:  'Solicitada',
    formalized: 'Formalizada',
    approved:   'Aprobada',
    confirmed:  'Confirmada',
    rejected:   'Rechazada',
  }[s] || s
}
function badge(s) {
  return {
    requested:  'bg-yellow-100 text-yellow-700',
    formalized: 'bg-orange-100 text-orange-700',
    approved:   'bg-blue-100 text-blue-700',
    confirmed:  'bg-green-100 text-green-700',
    rejected:   'bg-red-100 text-red-700',
  }[s] || 'bg-gray-100 text-gray-700'
}
function bc(s) {
  return {
    requested:  'border-yellow-400',
    formalized: 'border-orange-400',
    approved:   'border-blue-400',
    confirmed:  'border-green-400',
    rejected:   'border-red-400',
  }[s] || 'border-gray-300'
}

onMounted(() => {
  load()
  loadAccounts()
})
</script>
