<!--
  Módulo 6 — TransactionNewView.vue
  Formulario completo para registrar una transacción nueva: categoría, subcategoría,
  tipo, importe, concepto, proyecto/obra, contraparte y vehículo.
-->
<template>
  <div class="p-4 max-w-3xl mx-auto">
    <h1 class="text-xl font-bold mb-4">Nueva Transacción</h1>

    <div v-if="error" class="bg-red-100 text-red-700 p-3 rounded mb-4 text-sm">{{ error }}</div>
    <div v-if="success" class="bg-green-100 text-green-700 p-3 rounded mb-4 text-sm">
      Transacción {{ success }} registrada correctamente.
      <router-link :to="`/transactions`" class="underline ml-2">Ver listado</router-link>
    </div>

    <form @submit.prevent="submit" class="bg-white rounded shadow p-4 space-y-4">
      <!-- Tipo e importe -->
      <div class="grid grid-cols-2 gap-4">
        <div>
          <label class="block text-sm font-medium mb-1">Tipo *</label>
          <select v-model="form.type" class="w-full border rounded px-3 py-2" required>
            <option value="income">Ingreso</option>
            <option value="expense">Egreso</option>
          </select>
        </div>
        <div>
          <label class="block text-sm font-medium mb-1">Importe (XAF) *</label>
          <input v-model.number="form.amount" type="number" min="1" step="1"
                 class="w-full border rounded px-3 py-2" required />
        </div>
      </div>

      <!-- Concepto -->
      <div>
        <label class="block text-sm font-medium mb-1">Concepto *</label>
        <input v-model="form.concept" type="text" minlength="3"
               class="w-full border rounded px-3 py-2" required />
      </div>

      <!-- Categoría y subcategoría -->
      <div class="grid grid-cols-2 gap-4">
        <div>
          <label class="block text-sm font-medium mb-1">Categoría *</label>
          <select v-model="form.category_id" @change="loadSubcategories"
                  class="w-full border rounded px-3 py-2" required>
            <option :value="null" disabled>Seleccionar...</option>
            <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.name }}</option>
          </select>
        </div>
        <div>
          <label class="block text-sm font-medium mb-1">Subcategoría *</label>
          <select v-model="form.subcategory_id" class="w-full border rounded px-3 py-2" required>
            <option :value="null" disabled>Seleccionar...</option>
            <option v-for="s in subcategories" :key="s.id" :value="s.id">{{ s.name }}</option>
          </select>
        </div>
      </div>

      <!-- Proyecto y obra -->
      <div>
        <label class="block text-sm font-medium mb-1">Proyecto / Obra *</label>
        <ProjectWorkSelector v-model="form.projects" />
      </div>

      <!-- Contraparte -->
      <div>
        <label class="block text-sm font-medium mb-1">Contraparte *</label>
        <CounterpartySelector @update="onCounterpartyChange" />
      </div>

      <!-- Vehículo (opcional) -->
      <div>
        <label class="block text-sm font-medium mb-1">Vehículo (opcional)</label>
        <select v-model="form.vehicle_id" class="w-full border rounded px-3 py-2">
          <option :value="null">— Ninguno —</option>
          <option v-for="v in vehicles" :key="v.id" :value="v.id">{{ v.plate }} {{ v.brand || '' }}</option>
        </select>
      </div>

      <div class="flex justify-end gap-2 pt-2">
        <router-link to="/transactions" class="px-4 py-2 bg-gray-200 rounded hover:bg-gray-300 text-sm">
          Cancelar
        </router-link>
        <button type="submit" :disabled="submitting"
                class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 text-sm disabled:opacity-50">
          {{ submitting ? 'Registrando...' : 'Registrar Transacción' }}
        </button>
      </div>
    </form>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/services/api'
import transactionService from '@/services/transactionService'
import ProjectWorkSelector from '@/components/ProjectWorkSelector.vue'
import CounterpartySelector from '@/components/CounterpartySelector.vue'
import { useAuthStore } from '@/stores/auth'

// H-Role guard: solo gestor accede a /transactions/new
const __authGuard = useAuthStore()
const __routerGuard = useRouter()
onMounted(() => {
  if (!__authGuard.hasRole('gestor')) {
    __routerGuard.replace('/transactions')
  }
})

const router = useRouter()

const form = ref({
  type: 'expense', amount: null, concept: '',
  category_id: null, subcategory_id: null,
  projects: [{ project_id: null, work_id: null }],
  supplier_id: null, employee_id: null, partner_id: null,
  counterparty_free: null, vehicle_id: null
})

const categories = ref([])
const subcategories = ref([])
const vehicles = ref([])
const error = ref('')
const success = ref('')
const submitting = ref(false)

async function loadCategories() {
  const { data } = await api.get('/categories')
  categories.value = Array.isArray(data) ? data : (data.items || [])
}

async function loadSubcategories() {
  form.value.subcategory_id = null
  if (!form.value.category_id) { subcategories.value = []; return }
  const { data } = await api.get('/subcategories', { params: { category_id: form.value.category_id } })
  subcategories.value = Array.isArray(data) ? data : (data.items || [])
}

async function loadVehicles() {
  const { data } = await api.get('/vehicles')
  vehicles.value = Array.isArray(data) ? data : (data.items || [])
}

function onCounterpartyChange(cp) {
  form.value.supplier_id = cp.supplier_id
  form.value.employee_id = cp.employee_id
  form.value.partner_id = cp.partner_id
  form.value.counterparty_free = cp.counterparty_free
}

async function submit() {
  error.value = ''
  success.value = ''
  submitting.value = true
  try {
    const { data } = await transactionService.create(form.value)
    router.push('/transactions/' + data.id)
    // Reset del formulario
    form.value = {
      type: 'expense', amount: null, concept: '',
      category_id: null, subcategory_id: null,
      projects: [{ project_id: null, work_id: null }],
      supplier_id: null, employee_id: null, partner_id: null,
      counterparty_free: null, vehicle_id: null
    }
    subcategories.value = []
  } catch (e) {
    error.value = e.response?.data?.detail || 'Error al registrar la transacción'
  } finally {
    submitting.value = false
  }
}

onMounted(() => { loadCategories(); loadVehicles() })
</script>
