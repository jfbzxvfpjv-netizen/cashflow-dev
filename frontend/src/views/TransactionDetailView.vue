<!--
  Módulo 6 — TransactionDetailView.vue
  Detalle completo de una transacción con adjuntos, timer regresivo,
  aprobación/rechazo/cancelación y estado de integridad.
-->
<template>
  <div class="p-4 max-w-3xl mx-auto">
    <div class="flex items-center gap-3 mb-4">
      <router-link to="/transactions" class="text-blue-600 hover:underline text-sm">← Volver</router-link>
      <h1 class="text-xl font-bold">Transacción {{ txn?.reference_number }}</h1>
      <EditTimer v-if="txn" :seconds-remaining="txn.seconds_remaining" @expired="txn.is_editable = false" />
    </div>

    <div v-if="!txn" class="text-gray-400 py-8 text-center">Cargando...</div>

    <div v-else class="bg-white rounded shadow p-4 space-y-4">
      <!-- Estado -->
      <div class="flex gap-2 flex-wrap">
        <span v-if="txn.cancelled" class="bg-gray-200 text-gray-700 px-2 py-1 rounded text-xs">ANULADA</span>
        <span v-if="txn.approval_status === 'pending_approval'" class="bg-yellow-100 text-yellow-700 px-2 py-1 rounded text-xs">PENDIENTE APROBACIÓN</span>
        <span v-if="txn.approval_status === 'authorized'" class="bg-blue-100 text-blue-700 px-2 py-1 rounded text-xs">AUTORIZADA — Pendiente de ejecución</span>
        <span v-if="txn.approval_status === 'rejected'" class="bg-red-100 text-red-700 px-2 py-1 rounded text-xs">RECHAZADA</span>
        <span v-if="txn.imported" class="bg-purple-100 text-purple-700 px-2 py-1 rounded text-xs">IMPORTADA</span>
        <span :class="txn.type === 'income' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'"
              class="px-2 py-1 rounded text-xs uppercase">{{ txn.type === 'income' ? 'Ingreso' : 'Egreso' }}</span>
      </div>

      <!-- Datos principales -->
      <div class="grid grid-cols-2 gap-3 text-sm">
        <div><span class="text-gray-500">Importe:</span> <strong class="font-mono">{{ Number(txn.amount).toLocaleString() }} XAF</strong></div>
        <div><span class="text-gray-500">Delegación:</span> {{ txn.delegacion }}</div>
        <div><span class="text-gray-500">Categoría:</span> {{ txn.category_name }}</div>
        <div><span class="text-gray-500">Subcategoría:</span> {{ txn.subcategory_name }}</div>
        <div><span class="text-gray-500">Registrado por:</span> {{ txn.user_fullname }}</div>
        <div><span class="text-gray-500">Fecha:</span> {{ formatDate(txn.created_at) }}</div>
      </div>

      <div class="text-sm">
        <span class="text-gray-500">Concepto:</span>
        <p class="mt-1">{{ txn.concept }}</p>
      </div>

      <!-- Proyectos -->
      <div v-if="txn.projects && txn.projects.length" class="text-sm">
        <span class="text-gray-500">Proyectos / Obras:</span>
        <ul class="mt-1 list-disc ml-5">
          <li v-for="p in txn.projects" :key="p.project_id + '-' + p.work_id">
            {{ p.project_name }} → {{ p.work_name }}
          </li>
        </ul>
      </div>

      <!-- Adjuntos -->
      <div class="border-t pt-3">
        <h3 class="text-sm font-semibold mb-2">Adjuntos</h3>
        <FileUploader
          :transaction-id="txn.id"
          :can-upload="txn.is_editable && !txn.cancelled"
          @uploaded="load"
          @deleted="load"
        />
      </div>

      <!-- Hash -->
      <div class="text-xs text-gray-400 font-mono break-all">
        SHA-256: {{ txn.integrity_hash }}
      </div>

      <!-- Acciones -->
      <div class="flex gap-2 pt-2 border-t">
        <button v-if="isAdmin && txn.approval_status === 'pending_approval'"
                @click="approve" class="px-3 py-1.5 bg-green-600 text-white rounded text-sm hover:bg-green-700">
          ✓ Aprobar
        </button>
        <button v-if="isAdmin && txn.approval_status === 'pending_approval'"
                @click="showReject = true" class="px-3 py-1.5 bg-red-600 text-white rounded text-sm hover:bg-red-700">
          ✕ Rechazar
        </button>
        <button v-if="txn.approval_status === 'authorized' && canExecute"
                @click="executeTxn" class="px-3 py-1.5 bg-blue-600 text-white rounded text-sm hover:bg-blue-700">
          💰 Ejecutar pago
        </button>
        <button v-if="isAdmin && !txn.cancelled && txn.approval_status !== 'pending_approval'"
                @click="showCancel = true" class="px-3 py-1.5 bg-gray-600 text-white rounded text-sm hover:bg-gray-700">
          Anular
        </button>
      </div>

      <!-- Modal rechazo -->
      <div v-if="showReject" class="border rounded p-3 bg-red-50 space-y-2">
        <label class="block text-sm font-medium">Motivo del rechazo *</label>
        <textarea v-model="rejectReason" class="w-full border rounded px-3 py-2 text-sm" rows="2"></textarea>
        <div class="flex gap-2">
          <button @click="reject" :disabled="!rejectReason"
                  class="px-3 py-1.5 bg-red-600 text-white rounded text-sm disabled:opacity-50">Confirmar rechazo</button>
          <button @click="showReject = false" class="px-3 py-1.5 bg-gray-200 rounded text-sm">Cancelar</button>
        </div>
      </div>

      <!-- Modal cancelación -->
      <div v-if="showCancel" class="border rounded p-3 bg-gray-50 space-y-2">
        <label class="block text-sm font-medium">Motivo de la anulación *</label>
        <textarea v-model="cancelReason" class="w-full border rounded px-3 py-2 text-sm" rows="2"></textarea>
        <div class="flex gap-2">
          <button @click="cancelTxn" :disabled="!cancelReason"
                  class="px-3 py-1.5 bg-gray-700 text-white rounded text-sm disabled:opacity-50">Confirmar anulación</button>
          <button @click="showCancel = false" class="px-3 py-1.5 bg-gray-200 rounded text-sm">Cancelar</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import transactionService from '@/services/transactionService'
import EditTimer from '@/components/EditTimer.vue'
import FileUploader from '@/components/FileUploader.vue'

const route = useRoute()
const auth = useAuthStore()
const isAdmin = computed(() => auth.hasRole('admin'))
const canExecute = computed(() => auth.hasRole('gestor', 'admin'))

const txn = ref(null)
const showReject = ref(false)
const showCancel = ref(false)
const rejectReason = ref('')
const cancelReason = ref('')

function formatDate(iso) {
  if (!iso) return ''
  return new Date(iso).toLocaleString('es-ES')
}

async function load() {
  const { data } = await transactionService.get(route.params.id)
  txn.value = data
}

async function executeTxn() {
  await transactionService.execute(txn.value.id)
  await load()
}

async function approve() {
  await transactionService.approve(txn.value.id)
  await load()
}

async function reject() {
  await transactionService.reject(txn.value.id, rejectReason.value)
  showReject.value = false
  rejectReason.value = ''
  await load()
}

async function cancelTxn() {
  await transactionService.cancel(txn.value.id, cancelReason.value)
  showCancel.value = false
  cancelReason.value = ''
  await load()
}

onMounted(() => load())
</script>
