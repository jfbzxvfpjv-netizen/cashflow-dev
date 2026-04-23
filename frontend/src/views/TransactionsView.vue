<!--
  Módulo 6 — TransactionsView.vue
  Listado de transacciones con filtros inline, paginación, indicadores de estado
  (adjuntos, firmas, candado, aprobación, cancelada, importada) y exportación.
-->
<template>
  <div class="p-4 max-w-full">
    <div class="flex justify-between items-center mb-4">
      <h1 class="text-xl font-bold">Transacciones</h1>
      <router-link v-if="canCreate" to="/transactions/new"
                   class="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 text-sm">
        + Nueva Transacción
      </router-link>
    </div>

    <!-- Filtros — Categoría, subcategoría y contraparte añadidos -->
    <div class="bg-white rounded shadow p-3 mb-4 text-sm">
      <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2">
        <input v-model="filters.date_start" type="date" class="border rounded px-2 py-1" placeholder="Desde" />
        <input v-model="filters.date_end" type="date" class="border rounded px-2 py-1" placeholder="Hasta" />
        <select v-if="auth.hasRole('admin', 'contable')" v-model="filters.delegacion" class="border rounded px-2 py-1" @change="loadTransactions">
          <option value="">Todas las delegaciones</option>
          <option value="Bata">Bata</option>
          <option value="Malabo">Malabo</option>
        </select>
        <select v-model="filters.type" class="border rounded px-2 py-1">
          <option value="">Todos los tipos</option>
          <option value="income">Ingreso</option>
          <option value="expense">Egreso</option>
        </select>
        <select v-model="filters.category_id" class="border rounded px-2 py-1" @change="onCategoryChange">
          <option value="">Todas las categorías</option>
          <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.name }}</option>
        </select>
        <select v-model="filters.subcategory_id" class="border rounded px-2 py-1" :disabled="!filters.category_id">
          <option value="">Todas las subcategorías</option>
          <option v-for="sc in subcategories" :key="sc.id" :value="sc.id">{{ sc.name }}</option>
        </select>
        <select v-model="counterpartyFilter" class="border rounded px-2 py-1" @change="onCounterpartyChange">
          <option value="">Todas las contrapartes</option>
          <optgroup label="Proveedores">
            <option v-for="s in suppliers" :key="'s'+s.id" :value="'supplier_'+s.id">{{ s.name }}</option>
          </optgroup>
          <optgroup label="Empleados">
            <option v-for="e in employees" :key="'e'+e.id" :value="'employee_'+e.id">{{ e.full_name }}</option>
          </optgroup>
        </select>
      </div>
      <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2 mt-2">
        <select v-model="filters.approval_status" class="border rounded px-2 py-1">
          <option value="">Todos los estados</option>
          <option value="approved">Aprobadas</option>
          <option value="pending_approval">Pendientes</option>
          <option value="authorized">Autorizadas</option>
          <option value="rejected">Rechazadas</option>
        </select>
        <input v-model="filters.concept" type="text" class="border rounded px-2 py-1" placeholder="Buscar concepto..." />
        <div></div>
        <div></div>
        <button @click="resetFilters" class="bg-gray-100 hover:bg-gray-200 border rounded px-3 py-1 text-gray-500">Limpiar</button>
        <button @click="loadTransactions" class="bg-gray-200 hover:bg-gray-300 rounded px-3 py-1 font-medium">Filtrar</button>
      </div>
    </div>

    <!-- Tabla -->
    <div class="bg-white rounded shadow overflow-x-auto">
      <table class="w-full text-sm">
        <thead class="bg-gray-50 text-left">
          <tr>
            <th class="px-3 py-2">Fecha</th>
            <th class="px-3 py-2">Ref.</th>
            <th class="px-3 py-2">Concepto</th>
            <th class="px-3 py-2">Categoría</th>
            <th class="px-3 py-2">Contraparte</th>
            <th class="px-3 py-2 text-right">Importe</th>
            <th class="px-3 py-2 text-center">Estado</th>
            <th class="px-3 py-2 text-center">📎</th>
            <th class="px-3 py-2"></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="t in transactions" :key="t.id"
              class="border-t hover:bg-gray-50 cursor-pointer"
              :class="{ 'opacity-50 line-through': t.cancelled }"
              @click="$router.push(`/transactions/${t.id}`)">
            <td class="px-3 py-2 whitespace-nowrap">{{ formatDate(t.created_at) }}</td>
            <td class="px-3 py-2 font-mono text-xs">{{ t.reference_number }}</td>
            <td class="px-3 py-2 max-w-xs truncate">{{ t.concept }}</td>
            <td class="px-3 py-2 text-xs">{{ t.category_name }}</td>
            <td class="px-3 py-2 text-xs max-w-[180px] truncate" :title="t.counterparty_name">{{ t.counterparty_name || '—' }}</td>
            <td class="px-3 py-2 text-right font-mono"
                :class="t.type === 'income' ? 'text-green-600' : 'text-red-600'">
              {{ t.type === 'income' ? '+' : '-' }}{{ Number(t.amount).toLocaleString() }}
            </td>
            <td class="px-3 py-2 text-center">
              <span v-if="t.approval_status === 'pending_approval'"
                    class="bg-yellow-100 text-yellow-700 px-2 py-0.5 rounded text-xs">Pendiente</span>
              <span v-else-if="t.approval_status === 'authorized'"
                    class="bg-blue-100 text-blue-700 px-2 py-0.5 rounded text-xs">Autorizada</span>
              <span v-else-if="t.approval_status === 'rejected'"
                    class="bg-red-100 text-red-700 px-2 py-0.5 rounded text-xs">Rechazada</span>
              <span v-else-if="t.cancelled"
                    class="bg-gray-200 text-gray-600 px-2 py-0.5 rounded text-xs">Anulada</span>
              <span v-else class="text-green-500 text-xs">✓</span>
            </td>
            <td class="px-3 py-2 text-center text-xs">
              <span v-if="t.has_attachments">📎</span>
              <span v-if="t.has_signatures">✍</span>
            </td>
            <td class="px-3 py-2 text-center">
              <span v-if="t.is_editable" class="text-blue-500 text-xs">✏️</span>
              <span v-else class="text-gray-400 text-xs">🔒</span>
            </td>
          </tr>
          <tr v-if="transactions.length === 0">
            <td colspan="9" class="px-3 py-8 text-center text-gray-400">No hay transacciones</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Paginación -->
    <div v-if="totalPages > 1" class="flex justify-center gap-2 mt-4">
      <button v-for="p in totalPages" :key="p"
              @click="goToPage(p)"
              class="px-3 py-1 rounded text-sm"
              :class="p === currentPage ? 'bg-blue-600 text-white' : 'bg-gray-200 hover:bg-gray-300'">
        {{ p }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import transactionService from '@/services/transactionService'

const auth = useAuthStore()
const canCreate = computed(() => auth.hasRole('gestor'))

const transactions = ref([])
const currentPage = ref(1)
const totalPages = ref(1)
const filters = ref({
  delegacion: '', date_start: '', date_end: '', type: '', approval_status: '', concept: '',
  category_id: '', subcategory_id: '', supplier_id: '', employee_id: ''
})

// --- Catálogos para selectores de filtro ---
const categories = ref([])
const subcategories = ref([])
const suppliers = ref([])
const employees = ref([])
const counterpartyFilter = ref('')

const filteredSubcategories = computed(() => {
  if (!filters.value.category_id) return []
  const catId = Number(filters.value.category_id)
  return subcategories.value.filter(sc => sc.category_id === catId)
})

function onCategoryChange() {
  filters.value.subcategory_id = ''
  if (filters.value.category_id) {
    loadSubcategories(Number(filters.value.category_id))
  } else {
    subcategories.value = []
  }
}

function onCounterpartyChange() {
  const val = counterpartyFilter.value
  filters.value.supplier_id = ''
  filters.value.employee_id = ''
  if (val.startsWith('supplier_')) {
    filters.value.supplier_id = val.replace('supplier_', '')
  } else if (val.startsWith('employee_')) {
    filters.value.employee_id = val.replace('employee_', '')
  }
}

function resetFilters() {
  filters.value = {
    delegacion: '', date_start: '', date_end: '', type: '', approval_status: '', concept: '',
    category_id: '', subcategory_id: '', supplier_id: '', employee_id: ''
  }
  counterpartyFilter.value = ''
  subcategories.value = []
  loadTransactions()
}

async function loadFilterCatalogs() {
  try {
    const [catRes, supRes, empRes] = await Promise.all([
      transactionService.getCategories(),
      transactionService.getSuppliers(),
      transactionService.getEmployees()
    ])
    categories.value = catRes.data.items || catRes.data || []
    suppliers.value = supRes.data.items || supRes.data || []
    employees.value = empRes.data.items || empRes.data || []
  } catch (e) {
    console.error('Error cargando catálogos de filtros:', e)
  }
}

async function loadSubcategories(categoryId) {
  try {
    const res = await transactionService.getSubcategories({ category_id: categoryId })
    subcategories.value = res.data.items || res.data || []
  } catch (e) {
    subcategories.value = []
  }
}

function formatDate(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  return d.toLocaleDateString('es-ES', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

async function loadTransactions() {
  const params = { page: currentPage.value, page_size: 50 }
  Object.entries(filters.value).forEach(([k, v]) => {
    if (v !== '' && v !== null) params[k] = v
  })
  const { data } = await transactionService.list(params)
  transactions.value = data.items || []
  totalPages.value = data.pages || 1
  currentPage.value = data.page || 1
}

function goToPage(p) {
  currentPage.value = p
  loadTransactions()
}

onMounted(() => {
  loadFilterCatalogs()
  loadTransactions()
})
</script>
