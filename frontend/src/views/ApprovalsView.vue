<!--
  Módulo 6 — ApprovalsView.vue
  Panel de aprobaciones pendientes y configuración de umbrales por categoría.
-->
<template>
  <div class="p-4 max-w-4xl mx-auto">
    <h1 class="text-xl font-bold mb-4">Aprobaciones</h1>

    <!-- Pendientes -->
    <h2 class="text-lg font-semibold mb-2">Transacciones pendientes de aprobación</h2>
    <div class="bg-white rounded shadow mb-6 overflow-x-auto">
      <table class="w-full text-sm">
        <thead class="bg-yellow-50">
          <tr>
            <th class="px-3 py-2 text-left">Referencia</th>
            <th class="px-3 py-2 text-left">Concepto</th>
            <th class="px-3 py-2 text-right">Importe</th>
            <th class="px-3 py-2 text-left">Fecha</th>
            <th class="px-3 py-2"></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="a in pending" :key="a.id" class="border-t">
            <td class="px-3 py-2 font-mono text-xs">{{ a.reference_number }}</td>
            <td class="px-3 py-2">{{ a.concept }}</td>
            <td class="px-3 py-2 text-right font-mono">{{ Number(a.amount).toLocaleString() }}</td>
            <td class="px-3 py-2 text-xs">{{ new Date(a.requested_at).toLocaleDateString('es-ES') }}</td>
            <td class="px-3 py-2">
              <div class="flex items-center gap-2 justify-end">
                <button @click="doApprove(a.id)" :disabled="busy"
                        class="px-2 py-1 bg-green-600 hover:bg-green-700 text-white text-xs rounded disabled:opacity-50">
                  Aprobar
                </button>
                <button @click="openRejectModal(a)" :disabled="busy"
                        class="px-2 py-1 bg-red-100 hover:bg-red-200 text-red-700 text-xs rounded disabled:opacity-50">
                  Rechazar
                </button>
                <router-link :to="`/transactions/${a.transaction_id}`"
                             class="text-blue-600 hover:underline text-xs">Ver →</router-link>
              </div>
            </td>
          </tr>
          <tr v-if="pending.length === 0">
            <td colspan="5" class="px-3 py-6 text-center text-gray-400">Sin aprobaciones pendientes</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Umbrales -->
    <h2 class="text-lg font-semibold mb-2">Umbrales de aprobación por categoría</h2>
    <div class="bg-white rounded shadow overflow-x-auto">
      <table class="w-full text-sm">
        <thead class="bg-gray-50">
          <tr>
            <th class="px-3 py-2 text-left">Categoría</th>
            <th class="px-3 py-2 text-left">Delegación</th>
            <th class="px-3 py-2 text-right">Umbral (XAF)</th>
            <th class="px-3 py-2"></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="t in thresholds" :key="t.id" class="border-t">
            <td class="px-3 py-2">{{ t.category_name }}</td>
            <td class="px-3 py-2">{{ t.delegacion }}</td>
            <td class="px-3 py-2 text-right font-mono">{{ Number(t.threshold_amount).toLocaleString() }}</td>
            <td class="px-3 py-2">
              <button @click="removeThreshold(t.id)" class="text-red-500 hover:text-red-700 text-xs">Eliminar</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Nuevo umbral -->
    <div class="bg-white rounded shadow p-3 mt-4">
      <h3 class="text-sm font-semibold mb-2">Añadir umbral</h3>
      <div class="flex gap-2 items-end flex-wrap">
        <select v-model="newThreshold.category_id" class="border rounded px-2 py-1.5 text-sm">
          <option :value="null" disabled>Categoría...</option>
          <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.name }}</option>
        </select>
        <select v-model="newThreshold.delegacion" class="border rounded px-2 py-1.5 text-sm">
          <option value="Bata">Bata</option>
          <option value="Malabo">Malabo</option>
        </select>
        <input v-model.number="newThreshold.threshold_amount" type="number" min="1" placeholder="Importe"
               class="border rounded px-2 py-1.5 text-sm w-32" />
        <button @click="addThreshold" class="bg-blue-600 text-white px-3 py-1.5 rounded text-sm hover:bg-blue-700">
          Añadir
        </button>
      </div>
    </div>

    <!-- Modal Rechazar -->
    <div v-if="modal==='reject'" class="fixed inset-0 bg-black/40 flex items-center justify-center z-50" @click.self="modal=null">
      <div class="bg-white rounded-md p-6 w-full max-w-md">
        <h2 class="text-lg font-semibold mb-2">Rechazar aprobación</h2>
        <p class="text-xs text-gray-500 mb-3" v-if="rejectTarget">
          {{ rejectTarget.reference_number }} · {{ rejectTarget.concept }} · {{ Number(rejectTarget.amount).toLocaleString() }} XAF
        </p>
        <div v-if="merr" class="text-sm text-red-600 mb-2 p-2 bg-red-50 rounded">{{ merr }}</div>
        <label class="block text-xs font-medium text-gray-700 mb-1">Motivo del rechazo *</label>
        <textarea v-model="rejectReason" rows="3" class="w-full border rounded px-3 py-1.5 text-sm"
                  placeholder="Explica brevemente por qué se rechaza"></textarea>
        <div class="flex justify-end gap-2 mt-4">
          <button @click="modal=null" class="px-4 py-1.5 text-sm rounded border">Cancelar</button>
          <button @click="doReject" :disabled="busy"
                  class="px-4 py-1.5 text-sm rounded bg-red-600 text-white hover:bg-red-700 disabled:opacity-50">
            {{ busy ? 'Enviando…' : 'Rechazar' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/services/api'
import transactionService from '@/services/transactionService'

const pending = ref([])
const thresholds = ref([])
const categories = ref([])
const newThreshold = ref({ category_id: null, delegacion: 'Bata', threshold_amount: null })

// M10a: estado para botones aprobar/rechazar
const modal = ref(null)
const rejectTarget = ref(null)
const rejectReason = ref('')
const merr = ref('')
const busy = ref(false)

async function load() {
  const [p, t, c] = await Promise.all([
    transactionService.listPendingApprovals(),
    transactionService.listThresholds(),
    api.get('/categories')
  ])
  pending.value = p.data || []
  thresholds.value = t.data || []
  categories.value = Array.isArray(c.data) ? c.data : (c.data.items || [])
}

async function addThreshold() {
  await transactionService.createThreshold(newThreshold.value)
  newThreshold.value = { category_id: null, delegacion: 'Bata', threshold_amount: null }
  await load()
}

async function removeThreshold(id) {
  if (!confirm('¿Eliminar este umbral?')) return
  await transactionService.deleteThreshold(id)
  await load()
}

async function doApprove(approvalId) {
  if (!confirm('¿Aprobar esta transacción? La caja se verá afectada inmediatamente.')) return
  busy.value = true
  try {
    await transactionService.approveApproval(approvalId)
    await load()
  } catch (e) {
    alert(e.response?.data?.detail || 'Error al aprobar')
  } finally {
    busy.value = false
  }
}

function openRejectModal(item) {
  rejectTarget.value = item
  rejectReason.value = ''
  merr.value = ''
  modal.value = 'reject'
}

async function doReject() {
  if (!rejectReason.value || rejectReason.value.length < 5) {
    merr.value = 'El motivo debe tener al menos 5 caracteres'
    return
  }
  busy.value = true
  try {
    await transactionService.rejectApproval(rejectTarget.value.id, rejectReason.value)
    modal.value = null
    await load()
  } catch (e) {
    merr.value = e.response?.data?.detail || 'Error al rechazar'
  } finally {
    busy.value = false
  }
}

onMounted(() => load())
</script>
