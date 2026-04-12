<template>
  <div class="max-w-6xl mx-auto px-4 py-6">
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl font-bold text-gray-800">Retiradas bancarias</h1>
      <button v-if="canPropose" @click="modal='propose'" class="bg-blue-600 text-white px-5 py-2 rounded-lg hover:bg-blue-700">＋ Proponer retirada</button>
    </div>

    <!-- Filtros -->
    <div class="bg-white rounded-lg shadow p-4 mb-6 grid grid-cols-2 md:grid-cols-4 gap-3">
      <select v-model="f.delegacion" @change="load" class="border rounded px-3 py-2 text-sm"><option value="">Todas</option><option>Bata</option><option>Malabo</option></select>
      <select v-model="f.status" @change="load" class="border rounded px-3 py-2 text-sm"><option value="">Todos</option><option value="pending">Pendientes</option><option value="approved">Aprobadas</option><option value="confirmed">Confirmadas</option><option value="rejected">Rechazadas</option></select>
      <input v-model="f.ds" @change="load" type="date" class="border rounded px-3 py-2 text-sm" />
      <input v-model="f.de" @change="load" type="date" class="border rounded px-3 py-2 text-sm" />
    </div>

    <!-- Lista -->
    <div class="space-y-4">
      <div v-for="w in items" :key="w.id" class="bg-white rounded-lg shadow p-5 border-l-4" :class="bc(w.status)">
        <div class="flex justify-between items-start">
          <div>
            <div class="flex items-center gap-2 mb-1">
              <span class="font-semibold">{{ fmt(w.amount) }} XAF</span>
              <span class="text-xs px-2 py-0.5 rounded-full font-medium" :class="badge(w.status)">{{ label(w.status) }}</span>
              <span class="text-xs px-2 py-0.5 rounded bg-gray-100 text-gray-600">{{ w.delegacion }}</span>
            </div>
            <p class="text-sm text-gray-600">{{ w.account_bank_name }} — {{ w.account_number }}</p>
            <p class="text-sm text-gray-500">Cheque: {{ w.cheque_reference }}</p>
          </div>
          <div class="text-right text-xs text-gray-400"><p>{{ fmtDt(w.proposed_at) }}</p><p>{{ w.proposed_by_name }}</p></div>
        </div>
        <div class="mt-3 text-xs text-gray-500 space-y-1">
          <p v-if="w.approved_by_name">✓ Aprobada: {{ w.approved_by_name }} — {{ fmtDt(w.approved_at) }}</p>
          <p v-if="w.confirmed_by_name">✓ Recibida: {{ w.confirmed_by_name }} — {{ fmtDt(w.confirmed_at) }}</p>
          <p v-if="w.rejection_reason" class="text-red-600">✕ {{ w.rejection_reason }}</p>
        </div>
        <div class="mt-4 flex gap-2">
          <template v-if="isAdmin && w.status==='pending'">
            <button @click="doApprove(w.id)" class="bg-green-600 text-white text-sm px-4 py-1.5 rounded hover:bg-green-700">Aprobar</button>
            <button @click="rejectTarget=w.id;modal='reject'" class="bg-red-600 text-white text-sm px-4 py-1.5 rounded hover:bg-red-700">Rechazar</button>
          </template>
          <button v-if="isGestor && w.status==='approved'" @click="doConfirm(w.id)" class="bg-blue-600 text-white text-sm px-4 py-1.5 rounded hover:bg-blue-700">Confirmar recepción</button>
        </div>
      </div>
      <div v-if="!items.length" class="text-center text-gray-400 py-8">Sin retiradas</div>
    </div>

    <!-- Modal proponer -->
    <div v-if="modal==='propose'" class="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg shadow-xl p-6 w-full max-w-md">
        <h2 class="text-lg font-semibold mb-4">Proponer retirada</h2>
        <form @submit.prevent="doPropose" class="space-y-4">
          <select v-model="pf.delegacion" class="w-full border rounded px-3 py-2" required><option value="">— Delegación —</option><option>Bata</option><option>Malabo</option></select>
          <select v-model.number="pf.corporate_account_id" class="w-full border rounded px-3 py-2" required><option value="">— Cuenta —</option><option v-for="a in accounts" :key="a.id" :value="a.id">{{ a.bank_name }} — {{ a.account_number }}</option></select>
          <input v-model.number="pf.amount" type="number" min="1" class="w-full border rounded px-3 py-2" placeholder="Importe (XAF)" required />
          <input v-model="pf.cheque_reference" class="w-full border rounded px-3 py-2" placeholder="Referencia del cheque" required />
          <textarea v-model="pf.notes" rows="2" class="w-full border rounded px-3 py-2" placeholder="Notas (opcional)"></textarea>
          <p v-if="merr" class="text-sm text-red-600">{{ merr }}</p>
          <div class="flex justify-end gap-3">
            <button type="button" @click="modal=null" class="text-gray-600">Cancelar</button>
            <button type="submit" :disabled="busy" class="bg-blue-600 text-white px-5 py-2 rounded-lg disabled:opacity-50">{{ busy?'Enviando...':'Proponer' }}</button>
          </div>
        </form>
      </div>
    </div>

    <!-- Modal rechazar -->
    <div v-if="modal==='reject'" class="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg shadow-xl p-6 w-full max-w-md">
        <h2 class="text-lg font-semibold mb-4">Rechazar retirada</h2>
        <textarea v-model="rejectReason" rows="3" class="w-full border rounded px-3 py-2 mb-3" placeholder="Motivo del rechazo (obligatorio)"></textarea>
        <p v-if="merr" class="text-sm text-red-600 mb-3">{{ merr }}</p>
        <div class="flex justify-end gap-3">
          <button @click="modal=null" class="text-gray-600">Cancelar</button>
          <button @click="doReject" :disabled="busy" class="bg-red-600 text-white px-5 py-2 rounded-lg disabled:opacity-50">{{ busy?'Rechazando...':'Rechazar' }}</button>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import bwSvc from '@/services/bankWithdrawalService'
import api from '@/services/api'

const auth = useAuthStore()
const isAdmin = computed(() => auth.user?.role === 'admin')
const isGestor = computed(() => auth.user?.role === 'gestor')
const canPropose = computed(() => ['contable','admin'].includes(auth.user?.role))

const items = ref([]), accounts = ref([])
const f = ref({ delegacion:'', status:'', ds:'', de:'' })
const modal = ref(null), merr = ref(''), busy = ref(false)
const pf = ref({ delegacion:'', corporate_account_id:'', amount:'', cheque_reference:'', notes:'' })
const rejectTarget = ref(null), rejectReason = ref('')

onMounted(async () => { await load(); try { accounts.value = (await api.get('/corporate-accounts')).data } catch {} })
async function load() {
  const p = {}
  if (f.value.delegacion) p.delegacion = f.value.delegacion
  if (f.value.status) p.status = f.value.status
  if (f.value.ds) p.date_start = f.value.ds+'T00:00:00'
  if (f.value.de) p.date_end = f.value.de+'T23:59:59'
  try { items.value = (await bwSvc.list(p)).data.items } catch { items.value = [] }
}
async function doPropose() {
  merr.value=''; busy.value=true
  try { await bwSvc.propose(pf.value); modal.value=null; pf.value={delegacion:'',corporate_account_id:'',amount:'',cheque_reference:'',notes:''}; await load() }
  catch(e) { merr.value=e.response?.data?.detail||'Error' } finally { busy.value=false }
}
async function doApprove(id) { try { await bwSvc.approve(id,{}); await load() } catch(e) { alert(e.response?.data?.detail||'Error') } }
async function doReject() {
  if (!rejectReason.value.trim()) { merr.value='Motivo obligatorio'; return }
  busy.value=true
  try { await bwSvc.reject(rejectTarget.value,{rejection_reason:rejectReason.value}); modal.value=null; await load() }
  catch(e) { merr.value=e.response?.data?.detail||'Error' } finally { busy.value=false }
}
async function doConfirm(id) {
  if (!confirm('¿Confirma la recepción? Se generará un ingreso automático.')) return
  try { await bwSvc.confirm(id,{}); await load() } catch(e) { alert(e.response?.data?.detail||'Error') }
}
function fmt(n) { return new Intl.NumberFormat('es-GQ').format(n) }
function fmtDt(d) { return d ? new Date(d).toLocaleString('es-GQ',{day:'2-digit',month:'2-digit',year:'numeric',hour:'2-digit',minute:'2-digit'}) : '—' }
function label(s) { return {pending:'Pendiente',approved:'Aprobada',confirmed:'Confirmada',rejected:'Rechazada'}[s]||s }
function badge(s) { return {pending:'bg-yellow-100 text-yellow-700',approved:'bg-blue-100 text-blue-700',confirmed:'bg-green-100 text-green-700',rejected:'bg-red-100 text-red-700'}[s] }
function bc(s) { return {pending:'border-yellow-400',approved:'border-blue-400',confirmed:'border-green-400',rejected:'border-red-400'}[s] }
</script>
