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
              <router-link :to="`/transactions/${a.transaction_id}`"
                           class="text-blue-600 hover:underline text-xs">Ver detalle →</router-link>
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

onMounted(() => load())
</script>
