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
            <th class="px-3 py-2 text-right">Deducciones</th>
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
            <td class="px-3 py-2 text-right font-mono text-red-600 deduction-tooltip relative">
              <span v-if="totalDeductions(e) > 0" :title="deductionDetail(e)" class="cursor-help underline decoration-dotted">
                -{{ totalDeductions(e).toLocaleString() }}
              </span>
              <span v-else class="text-gray-300">—</span>
            </td>
            <td class="px-3 py-2 text-right font-mono font-semibold">{{ Number(e.cash_amount).toLocaleString() }}</td>
            <td class="px-3 py-2">
              <span v-if="e.liquidated_without_cash" class="text-purple-700 text-xs">
                Liquidado sin caja · {{ fmtDate(e.liquidated_at) }}
              </span>
              <span v-else-if="!e.transaction_id && Number(e.cash_amount) === 0 && totalDeductions(e) === 0" class="text-gray-400 text-xs">
                Sin efectivo (todo por banco)
              </span>
              <span v-else-if="!e.transaction_id && Number(e.cash_amount) === 0 && totalDeductions(e) > 0" class="text-orange-600 text-xs">
                Pendiente (sin efectivo)
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
              <button v-if="canLiquidateNoCash(e)" @click="openLiquidateModal(e)"
                      class="px-2 py-1 bg-purple-600 hover:bg-purple-700 text-white text-xs rounded">
                Liquidar sin caja
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
        <div class="bg-gray-50 rounded p-3 mb-3 text-sm desglose-pago">
          <div class="flex justify-between"><span class="text-gray-500">Periodo:</span>
            <span>{{ monthNames[period.month - 1] }} {{ period.year }}</span></div>
          <div class="border-t border-gray-200 my-2"></div>
          <div class="flex justify-between"><span class="text-gray-500">Salario bruto:</span>
            <span class="font-mono">{{ Number(payTarget.salary_gross).toLocaleString() }} XAF</span></div>
          <div v-if="Number(payTarget.salary_transfer) > 0" class="flex justify-between"><span class="text-gray-500">Transferencia bancaria:</span>
            <span class="font-mono text-gray-500">-{{ Number(payTarget.salary_transfer).toLocaleString() }} XAF</span></div>
          <div v-if="Number(payTarget.deduction_advances) > 0" class="flex justify-between"><span class="text-gray-500">Anticipos pendientes:</span>
            <span class="font-mono text-red-600">-{{ Number(payTarget.deduction_advances).toLocaleString() }} XAF</span></div>
          <div v-if="Number(payTarget.deduction_loans) > 0" class="flex justify-between"><span class="text-gray-500">Cuotas de préstamos:</span>
            <span class="font-mono text-red-600">-{{ Number(payTarget.deduction_loans).toLocaleString() }} XAF</span></div>
          <div v-if="Number(payTarget.deduction_retentions) > 0" class="flex justify-between"><span class="text-gray-500">Retenciones liberadas:</span>
            <span class="font-mono text-red-600">-{{ Number(payTarget.deduction_retentions).toLocaleString() }} XAF</span></div>
          <div v-if="payTarget.deduction_refs && (payTarget.deduction_refs.advances?.length || payTarget.deduction_refs.loans?.length || payTarget.deduction_refs.retentions?.length)" class="text-xs text-gray-500 mt-2 pl-2 border-l-2 border-gray-200">
            <div v-for="adv in (payTarget.deduction_refs.advances || [])" :key="'a'+adv.advance_id">
              · Anticipo #{{ adv.advance_id }}: {{ Number(adv.amount).toLocaleString() }} XAF
            </div>
            <div v-for="loan in (payTarget.deduction_refs.loans || [])" :key="'l'+loan.loan_id">
              · Préstamo #{{ loan.loan_id }}: {{ Number(loan.amount).toLocaleString() }} XAF<span v-if="loan.installments"> (cuota de {{ loan.installments }})</span>
            </div>
            <div v-for="ret in (payTarget.deduction_refs.retentions || [])" :key="'r'+ret.retention_id">
              · Retención #{{ ret.retention_id }}: {{ Number(ret.amount).toLocaleString() }} XAF
            </div>
          </div>
          <div class="border-t border-gray-200 my-2"></div>
          <div class="flex justify-between text-base"><span class="font-semibold">Efectivo a pagar:</span>
            <span class="font-mono font-bold text-orange-700">{{ Number(payTarget.cash_amount).toLocaleString() }} XAF</span></div>
          <div v-if="payTarget.manual_override" class="text-xs text-blue-600 mt-1 italic">⚠ Admin ajustó manualmente. Las deducciones no se liquidarán automáticamente.</div>
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

    <!-- Modal Liquidar sin caja -->
    <div v-if="liquidateTarget" class="fixed inset-0 bg-black/40 flex items-start justify-center z-50 overflow-auto p-4" @click.self="closeLiquidateModal">
      <div class="bg-white rounded p-6 w-full max-w-lg my-4">
        <h2 class="text-lg font-semibold mb-1">Liquidar deducciones sin caja</h2>
        <p class="text-sm text-gray-600 mb-3">{{ liquidateTarget.employee_name }}</p>
        <div class="bg-purple-50 border-l-4 border-purple-400 p-3 mb-3 text-sm">
          <div class="font-semibold mb-1">⚠ Esta operación NO genera movimiento de caja.</div>
          <div>Se descontará del saldo de los anticipos / préstamos del empleado y se marcarán las retenciones aplicables como liberadas, sin pagar nada en efectivo.</div>
        </div>
        <div class="bg-gray-50 rounded p-3 mb-3 text-sm">
          <div class="flex justify-between"><span class="text-gray-500">Periodo:</span>
            <span>{{ monthNames[period.month - 1] }} {{ period.year }}</span></div>
          <div class="flex justify-between"><span class="text-gray-500">Salario bruto:</span>
            <span class="font-mono">{{ Number(liquidateTarget.salary_gross).toLocaleString() }} XAF</span></div>
          <div v-if="Number(liquidateTarget.deduction_advances) > 0" class="flex justify-between"><span class="text-gray-500">Anticipos:</span>
            <span class="font-mono text-red-600">-{{ Number(liquidateTarget.deduction_advances).toLocaleString() }} XAF</span></div>
          <div v-if="Number(liquidateTarget.deduction_loans) > 0" class="flex justify-between"><span class="text-gray-500">Cuotas de préstamos:</span>
            <span class="font-mono text-red-600">-{{ Number(liquidateTarget.deduction_loans).toLocaleString() }} XAF</span></div>
          <div v-if="Number(liquidateTarget.deduction_retentions) > 0" class="flex justify-between"><span class="text-gray-500">Retenciones:</span>
            <span class="font-mono text-red-600">-{{ Number(liquidateTarget.deduction_retentions).toLocaleString() }} XAF</span></div>
          <div class="border-t border-gray-200 my-2"></div>
          <div class="flex justify-between text-base">
            <span class="font-semibold">Total a liquidar:</span>
            <span class="font-mono font-bold text-purple-700">{{ totalDeductions(liquidateTarget).toLocaleString() }} XAF</span>
          </div>
          <div class="flex justify-between text-sm mt-1">
            <span class="text-gray-500">Efectivo a pagar:</span>
            <span class="font-mono text-gray-400">0 XAF</span>
          </div>
        </div>
        <div v-if="liquidateErr" class="text-sm text-red-600 mb-2 p-2 bg-red-50 rounded">{{ liquidateErr }}</div>
        <div class="flex justify-end gap-2 mt-4">
          <button @click="closeLiquidateModal" :disabled="liquidateBusy" class="px-4 py-1.5 text-sm rounded border">Cancelar</button>
          <button @click="doLiquidateNoCash" :disabled="liquidateBusy"
                  class="px-4 py-1.5 text-sm rounded bg-purple-600 text-white hover:bg-purple-700 disabled:opacity-50">
            {{ liquidateBusy ? 'Liquidando...' : 'Confirmar liquidación' }}
          </button>
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


function totalDeductions(e) {
  return Number(e.deduction_advances || 0) + Number(e.deduction_loans || 0) + Number(e.deduction_retentions || 0)
}
function deductionDetail(e) {
  const parts = []
  if (Number(e.deduction_advances || 0) > 0) parts.push(`Anticipos: ${Number(e.deduction_advances).toLocaleString()} XAF`)
  if (Number(e.deduction_loans || 0) > 0) parts.push(`Cuotas de préstamos: ${Number(e.deduction_loans).toLocaleString()} XAF`)
  if (Number(e.deduction_retentions || 0) > 0) parts.push(`Retenciones: ${Number(e.deduction_retentions).toLocaleString()} XAF`)
  const refs = e.deduction_refs || {}
  const detailLines = []
  for (const adv of (refs.advances || [])) {
    detailLines.push(`  · Anticipo #${adv.advance_id}: ${Number(adv.amount).toLocaleString()} XAF`)
  }
  for (const loan of (refs.loans || [])) {
    detailLines.push(`  · Préstamo #${loan.loan_id}: ${Number(loan.amount).toLocaleString()} XAF` +
      (loan.installments ? ` (cuota mensual de ${loan.installments})` : ''))
  }
  for (const ret of (refs.retentions || [])) {
    detailLines.push(`  · Retención #${ret.retention_id}: ${Number(ret.amount).toLocaleString()} XAF`)
  }
  return parts.join(' | ') + (detailLines.length ? '\n\nDetalle:\n' + detailLines.join('\n') : '')
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

// M10b-v3: liquidar sin caja
const liquidateTarget = ref(null)
const liquidateBusy = ref(false)
const liquidateErr = ref('')

function canLiquidateNoCash(e) {
  return !e.transaction_id
    && !e.liquidated_without_cash
    && Number(e.cash_amount) === 0
    && totalDeductions(e) > 0
    && auth.userRole === 'gestor'
    && period.value?.delegacion === auth.user?.delegacion
    && period.value?.status === 'draft'
}
function openLiquidateModal(e) {
  liquidateTarget.value = e
  liquidateErr.value = ''
}
function closeLiquidateModal() {
  liquidateTarget.value = null
  liquidateErr.value = ''
}
async function doLiquidateNoCash() {
  if (!liquidateTarget.value) return
  liquidateBusy.value = true
  liquidateErr.value = ''
  try {
    await payrollService.liquidateNoCash(period.value.id, liquidateTarget.value.id)
    closeLiquidateModal()
    await loadPeriod()
  } catch (e) {
    liquidateErr.value = e.response?.data?.detail || e.message
  } finally {
    liquidateBusy.value = false
  }
}
function fmtDate(iso) {
  if (!iso) return ''
  return new Date(iso).toLocaleDateString('es-ES', { day: '2-digit', month: '2-digit', year: 'numeric' })
}
</script>
