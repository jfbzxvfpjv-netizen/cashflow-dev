<!--
  EmployeesView.vue — /employees
  Gestión de empleados con actualización de salario y visualización de historial.
  Los datos salariales solo son visibles para admin y contable.
  Filtrado automático por delegación para Gestor de Caja.
-->
<template>
  <div class="p-6 max-w-6xl mx-auto">
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-semibold text-gray-900">Empleados</h1>
      <button
        v-if="isAdmin"
        class="px-4 py-2 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700"
        @click="openModal(null)"
      >
        + Nuevo empleado
      </button>
    </div>

    <!-- Filtros -->
    <div class="flex flex-wrap gap-3 mb-4">
      <input
        v-model="search"
        type="text"
        placeholder="Buscar por nombre, código o departamento..."
        class="flex-1 min-w-[250px] rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        @input="debouncedFetch"
      />
      <select
        v-if="canFilterDelegacion"
        v-model="delegacionFilter"
        class="rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        @change="fetchEmployees"
      >
        <option value="">Todas las delegaciones</option>
        <option value="Bata">Bata</option>
        <option value="Malabo">Malabo</option>
      </select>
    </div>

    <!-- Tabla de empleados -->
    <div class="bg-white border border-gray-200 rounded-lg overflow-hidden">
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Código</th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Nombre</th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Departamento</th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Delegación</th>
            <th v-if="canSeeSalary" class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Salario bruto</th>
            <th v-if="canSeeSalary" class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Parte transfer.</th>
            <th class="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Anticipo</th>
            <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Acciones</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-200">
          <tr v-for="emp in employees" :key="emp.id" :class="{ 'text-gray-400': !emp.active }">
            <td class="px-4 py-3 text-sm font-mono">{{ emp.code }}</td>
            <td class="px-4 py-3 text-sm font-medium">{{ emp.full_name }}</td>
            <td class="px-4 py-3 text-sm">{{ emp.department || '—' }}</td>
            <td class="px-4 py-3 text-sm">
              <span :class="emp.delegacion === 'Bata' ? 'text-blue-600' : 'text-green-600'">
                {{ emp.delegacion }}
              </span>
            </td>
            <td v-if="canSeeSalary" class="px-4 py-3 text-sm text-right font-mono">
              {{ formatXAF(emp.salary_gross) }}
            </td>
            <td v-if="canSeeSalary" class="px-4 py-3 text-sm text-right font-mono">
              {{ formatXAF(emp.salary_transfer) }}
            </td>
            <td class="px-4 py-3 text-sm text-center">
              <span v-if="emp.advance_pending" class="text-orange-600 font-medium">
                {{ formatXAF(emp.advance_amount) }}
              </span>
              <span v-else class="text-gray-300">—</span>
            </td>
            <td class="px-4 py-3 text-sm text-right space-x-2">
              <button
                v-if="isAdmin"
                class="text-blue-600 hover:text-blue-800"
                @click="openModal(emp)"
              >
                Editar
              </button>
              <button
                v-if="canSeeSalary"
                class="text-purple-600 hover:text-purple-800"
                @click="openSalaryModal(emp)"
              >
                Salario
              </button>
              <button
                v-if="canSeeSalary"
                class="text-gray-500 hover:text-gray-700"
                @click="showHistory(emp)"
              >
                Historial
              </button>
              <button
                v-if="isAdmin"
                class="text-sm"
                :class="emp.active ? 'text-red-500 hover:text-red-700' : 'text-green-500 hover:text-green-700'"
                @click="toggleActive(emp)"
              >
                {{ emp.active ? 'Desactivar' : 'Activar' }}
              </button>
              <button
                v-if="isAdmin"
                class="text-sm text-red-600 hover:text-red-800"
                @click="confirmDelete(emp)"
              >
                Eliminar
              </button>
            </td>
          </tr>
          <tr v-if="!employees.length">
            <td :colspan="canSeeSalary ? 8 : 6" class="px-4 py-8 text-center text-gray-400 text-sm">
              No se encontraron empleados
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Paginación -->
    <div v-if="totalPages > 1" class="flex items-center justify-between mt-4 text-sm text-gray-600">
      <span>{{ total }} empleados — Página {{ page }} de {{ totalPages }}</span>
      <div class="flex gap-2">
        <button :disabled="page <= 1" class="px-3 py-1 border rounded-md disabled:opacity-40" @click="page--; fetchEmployees()">←</button>
        <button :disabled="page >= totalPages" class="px-3 py-1 border rounded-md disabled:opacity-40" @click="page++; fetchEmployees()">→</button>
      </div>
    </div>

    <!-- Modal crear/editar empleado -->
    <Teleport to="body">
      <div v-if="showModal" class="fixed inset-0 bg-black/40 flex items-center justify-center z-50" @click.self="showModal = false">
        <div class="bg-white rounded-lg shadow-xl w-full max-w-lg mx-4 p-6 max-h-[90vh] overflow-y-auto">
          <h2 class="text-lg font-semibold mb-4">{{ editing ? 'Editar' : 'Nuevo' }} empleado</h2>
          <div class="space-y-3">
            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Código *</label>
                <input v-model="form.code" type="text" class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" :disabled="editing" />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Delegación *</label>
                <select v-model="form.delegacion" class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
                  <option value="Bata">Bata</option>
                  <option value="Malabo">Malabo</option>
                </select>
              </div>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Nombre completo *</label>
              <input v-model="form.full_name" type="text" class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Departamento</label>
                <input v-model="form.department" type="text" class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Puesto</label>
                <input v-model="form.position" type="text" class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
              </div>
            </div>
            <!-- Salario solo al crear -->
            <template v-if="!editing">
              <div class="grid grid-cols-2 gap-3">
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">Salario bruto (XAF)</label>
                  <input v-model.number="form.salary_gross" type="number" min="0" class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
                </div>
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">Parte transferencia</label>
                  <input v-model.number="form.salary_transfer" type="number" min="0" class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
                </div>
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Fecha efectiva salario</label>
                <input v-model="form.salary_effective_date" type="date" class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
              </div>
            </template>
          </div>
          <p v-if="formError" class="text-sm text-red-600 mt-2">{{ formError }}</p>
          <div class="flex justify-end gap-3 mt-4">
            <button class="px-4 py-2 text-sm text-gray-600" @click="showModal = false">Cancelar</button>
            <button class="px-4 py-2 text-sm bg-blue-600 text-white rounded-md" @click="saveEmployee">Guardar</button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Modal actualizar salario -->
    <Teleport to="body">
      <div v-if="showSalaryModal" class="fixed inset-0 bg-black/40 flex items-center justify-center z-50" @click.self="showSalaryModal = false">
        <div class="bg-white rounded-lg shadow-xl w-full max-w-sm mx-4 p-6">
          <h2 class="text-lg font-semibold mb-4">Actualizar salario — {{ salaryEmployee?.full_name }}</h2>
          <div class="space-y-3">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Salario bruto (XAF)</label>
              <input v-model.number="salaryForm.salary_gross" type="number" min="0" class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Parte transferencia (XAF)</label>
              <input v-model.number="salaryForm.salary_transfer" type="number" min="0" class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Fecha efectiva</label>
              <input v-model="salaryForm.salary_effective_date" type="date" class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
          </div>
          <p v-if="salaryError" class="text-sm text-red-600 mt-2">{{ salaryError }}</p>
          <div class="flex justify-end gap-3 mt-4">
            <button class="px-4 py-2 text-sm text-gray-600" @click="showSalaryModal = false">Cancelar</button>
            <button class="px-4 py-2 text-sm bg-purple-600 text-white rounded-md" @click="saveSalary">Guardar</button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Modal historial salarial -->
    <Teleport to="body">
      <div v-if="showHistoryModal" class="fixed inset-0 bg-black/40 flex items-center justify-center z-50" @click.self="showHistoryModal = false">
        <div class="bg-white rounded-lg shadow-xl w-full max-w-md mx-4 p-6 max-h-[80vh] overflow-y-auto">
          <h2 class="text-lg font-semibold mb-4">Historial salarial — {{ historyEmployee?.full_name }}</h2>
          <table class="min-w-full divide-y divide-gray-200 text-sm">
            <thead>
              <tr>
                <th class="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Fecha</th>
                <th class="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase">Bruto</th>
                <th class="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase">Transfer.</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-100">
              <tr v-for="h in salaryHistory" :key="h.id">
                <td class="px-3 py-2">{{ h.effective_date }}</td>
                <td class="px-3 py-2 text-right font-mono">{{ formatXAF(h.salary_gross) }}</td>
                <td class="px-3 py-2 text-right font-mono">{{ formatXAF(h.salary_transfer) }}</td>
              </tr>
            </tbody>
          </table>
          <div class="flex justify-end mt-4">
            <button class="px-4 py-2 text-sm text-gray-600" @click="showHistoryModal = false">Cerrar</button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
    <!-- Modal confirmación eliminar -->
    <div v-if="showDeleteConfirm" class="fixed inset-0 bg-black/40 flex items-center justify-center z-50" @click.self="showDeleteConfirm = false">
      <div class="bg-white rounded-lg shadow-xl p-6 w-full max-w-sm mx-4">
        <h3 class="text-lg font-semibold text-gray-900 mb-2">Confirmar eliminación</h3>
        <p class="text-sm text-gray-600 mb-2">¿Eliminar permanentemente a <strong>{{ deletingEmployee?.full_name }}</strong>?</p>
        <p class="text-xs text-gray-500 mb-4">Solo es posible si no tiene transacciones vinculadas.</p>
        <p v-if="deleteError" class="text-sm text-red-600 mb-3 bg-red-50 p-2 rounded">{{ deleteError }}</p>
        <div class="flex justify-end gap-3">
          <button class="px-4 py-2 text-sm text-gray-600 hover:text-gray-800" @click="showDeleteConfirm = false">Cancelar</button>
          <button class="px-4 py-2 text-sm bg-red-600 text-white rounded-md hover:bg-red-700" @click="executeDelete">Eliminar</button>
        </div>
      </div>
    </div>
  
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { employeesApi } from '@/api/catalogs'

const authStore = useAuthStore()
const isAdmin = computed(() => authStore.user?.role === 'admin')
const canSeeSalary = computed(() => ['admin', 'contable'].includes(authStore.user?.role))
const canFilterDelegacion = computed(() => authStore.user?.role !== 'gestor')

const employees = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = 50
const search = ref('')
const delegacionFilter = ref('')
const totalPages = computed(() => Math.ceil(total.value / pageSize))

// Modal empleado
const showModal = ref(false)
const editing = ref(false)
const editingId = ref(null)
const form = ref({})
const formError = ref('')

// Modal salario
const showSalaryModal = ref(false)
const salaryEmployee = ref(null)
const salaryForm = ref({})
const salaryError = ref('')

// Modal historial
const showHistoryModal = ref(false)
const showDeleteConfirm = ref(false)
const deletingEmployee = ref(null)
const deleteError = ref('')
const historyEmployee = ref(null)
const salaryHistory = ref([])

let searchTimeout = null

function formatXAF(amount) {
  if (amount == null) return '—'
  return new Intl.NumberFormat('es-GQ', { style: 'decimal', minimumFractionDigits: 0 }).format(amount) + ' XAF'
}

function debouncedFetch() {
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => { page.value = 1; fetchEmployees() }, 300)
}

async function fetchEmployees() {
  try {
    const params = { page: page.value, page_size: pageSize, active_only: false }
    if (search.value) params.search = search.value
    if (delegacionFilter.value) params.delegacion = delegacionFilter.value
    const { data } = await employeesApi.list(params)
    employees.value = data.items
    total.value = data.total
  } catch (err) {
    console.error('Error cargando empleados:', err)
  }
}

function openModal(emp) {
  editing.value = !!emp
  editingId.value = emp?.id || null
  form.value = emp
    ? { code: emp.code, full_name: emp.full_name, department: emp.department, position: emp.position, delegacion: emp.delegacion }
    : { code: '', full_name: '', department: '', position: '', delegacion: 'Bata', salary_gross: 0, salary_transfer: 0, salary_effective_date: new Date().toISOString().slice(0, 10) }
  formError.value = ''
  showModal.value = true
}

async function saveEmployee() {
  formError.value = ''
  try {
    if (editing.value) {
      await employeesApi.update(editingId.value, form.value)
    } else {
      await employeesApi.create(form.value)
    }
    showModal.value = false
    fetchEmployees()
  } catch (err) {
    formError.value = err.response?.data?.detail || 'Error al guardar'
  }
}

function openSalaryModal(emp) {
  salaryEmployee.value = emp
  salaryForm.value = {
    salary_gross: emp.salary_gross || 0,
    salary_transfer: emp.salary_transfer || 0,
    salary_effective_date: new Date().toISOString().slice(0, 10),
  }
  salaryError.value = ''
  showSalaryModal.value = true
}

async function saveSalary() {
  salaryError.value = ''
  try {
    await employeesApi.updateSalary(salaryEmployee.value.id, salaryForm.value)
    showSalaryModal.value = false
    fetchEmployees()
  } catch (err) {
    salaryError.value = err.response?.data?.detail || 'Error al actualizar salario'
  }
}

async function showHistory(emp) {
  historyEmployee.value = emp
  try {
    const { data } = await employeesApi.getSalaryHistory(emp.id)
    salaryHistory.value = data
    showHistoryModal.value = true
  } catch (err) {
    console.error('Error cargando historial:', err)
  }
}

onMounted(fetchEmployees)


// ── Toggle activar/desactivar y delete (parche toggle_delete_catalogos) ──
async function toggleActive(emp) {
  try {
    await employeesApi.update(emp.id, { active: !emp.active })
    fetchEmployees()
  } catch (e) {
    alert(e.response?.data?.detail || 'Error al cambiar estado')
  }
}

function confirmDelete(emp) {
  deletingEmployee.value = emp
  deleteError.value = ''
  showDeleteConfirm.value = true
}

async function executeDelete() {
  if (!deletingEmployee.value) return
  try {
    await employeesApi.delete(deletingEmployee.value.id)
    showDeleteConfirm.value = false
    deletingEmployee.value = null
    deleteError.value = ''
    fetchEmployees()
  } catch (e) {
    deleteError.value = e.response?.data?.detail || 'Error al eliminar'
  }
}

</script>
